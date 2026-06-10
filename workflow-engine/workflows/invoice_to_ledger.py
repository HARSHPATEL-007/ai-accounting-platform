from temporalio import workflow
from datetime import timedelta
from shared.models import InvoiceToLedgerInput, InvoiceToLedgerResult, WorkflowStatus
from activities.ocr_activities import (
    classify_document, extract_document_data, validate_extracted_data,
    create_ledger_entry, reconcile_with_bank, notify_human_review
)
import structlog

logger = structlog.get_logger("workflow_engine")

@workflow.defn
class InvoiceToLedgerWorkflow:
    """Straight-Through Processing workflow: Invoice -> OCR -> Validate -> Ledger -> Reconcile."""

    @workflow.run
    async def run(self, input_data: InvoiceToLedgerInput) -> InvoiceToLedgerResult:
        workflow_id = workflow.info().workflow_id
        run_id = workflow.info().run_id
        result = InvoiceToLedgerResult(
            workflow_id=workflow_id,
            run_id=run_id,
            status=WorkflowStatus.RUNNING,
            document_id=input_data.document_id,
            started_at=workflow.now()
        )

        try:
            # Step 1: Classify document
            classification = await workflow.execute_activity(
                classify_document,
                args=(input_data.document_id, input_data.s3_key),
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=workflow.retry_policy(
                    initial_interval=timedelta(seconds=1),
                    maximum_interval=timedelta(seconds=10),
                    maximum_attempts=5,
                    non_retryable_error_types=["ApplicationError"]
                )
            )
            result.steps_completed.append("classify")

            # Step 2: Extract data
            extracted = await workflow.execute_activity(
                extract_document_data,
                args=(input_data.document_id, input_data.s3_key),
                start_to_close_timeout=timedelta(seconds=60),
                retry_policy=workflow.retry_policy(maximum_attempts=3)
            )
            result.extracted_data = extracted
            result.steps_completed.append("extract")

            # Step 3: Validate
            validation = await workflow.execute_activity(
                validate_extracted_data,
                args=(extracted,),
                start_to_close_timeout=timedelta(seconds=10),
                retry_policy=workflow.retry_policy(maximum_attempts=2)
            )
            result.validation_result = validation
            result.steps_completed.append("validate")

            # If validation fails, flag for human review
            if not validation.get("valid", False):
                await workflow.execute_activity(
                    notify_human_review,
                    args=(input_data.document_id, validation.get("errors", ["Validation failed"])),
                    start_to_close_timeout=timedelta(seconds=10)
                )
                result.status = WorkflowStatus.FAILED
                result.error_message = f"Validation failed: {validation.get('errors')}"
                result.completed_at = workflow.now()
                return result

            # Step 4: Create ledger entry (if auto_post enabled)
            if input_data.auto_post:
                ledger = await workflow.execute_activity(
                    create_ledger_entry,
                    args=(input_data.client_id, extracted, input_data.document_id, input_data.uploaded_by),
                    start_to_close_timeout=timedelta(seconds=10),
                    retry_policy=workflow.retry_policy(maximum_attempts=3)
                )
                result.ledger_entry_id = ledger.get("id")
                result.steps_completed.append("ledger_post")

                # Step 5: Reconcile with bank
                reconciliation = await workflow.execute_activity(
                    reconcile_with_bank,
                    args=(input_data.client_id, result.ledger_entry_id),
                    start_to_close_timeout=timedelta(seconds=15)
                )
                result.reconciliation_status = reconciliation.get("status")
                result.steps_completed.append("reconcile")
            else:
                # Flag for human approval before posting
                await workflow.execute_activity(
                    notify_human_review,
                    args=(input_data.document_id, "Awaiting human approval for ledger posting"),
                    start_to_close_timeout=timedelta(seconds=10)
                )

            result.status = WorkflowStatus.COMPLETED
            result.completed_at = workflow.now()

        except Exception as e:
            logger.error("workflow_failed", workflow_id=workflow_id, error=str(e))
            result.status = WorkflowStatus.FAILED
            result.error_message = str(e)
            result.completed_at = workflow.now()

            # Saga compensation: rollback ledger entry if created
            if result.ledger_entry_id:
                await workflow.execute_activity(
                    notify_human_review,
                    args=(input_data.document_id, f"Workflow failed, rollback required for ledger {result.ledger_entry_id}"),
                    start_to_close_timeout=timedelta(seconds=10)
                )

        return result
