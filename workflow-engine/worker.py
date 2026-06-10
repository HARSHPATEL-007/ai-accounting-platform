import asyncio
import os
from temporalio.client import Client
from temporalio.worker import Worker
from workflows.invoice_to_ledger import InvoiceToLedgerWorkflow
from activities import ocr_activities

async def main():
    client = await Client.connect(os.getenv("TEMPORAL_HOST", "temporal:7233"))

    worker = Worker(
        client,
        task_queue="accounting-stp-queue",
        workflows=[InvoiceToLedgerWorkflow],
        activities=[
            ocr_activities.classify_document,
            ocr_activities.extract_document_data,
            ocr_activities.validate_extracted_data,
            ocr_activities.create_ledger_entry,
            ocr_activities.reconcile_with_bank,
            ocr_activities.notify_human_review,
        ],
    )

    print("Worker started, listening on task queue: accounting-stp-queue")
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())
