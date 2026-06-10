export interface Client {
  id: string;
  type: "startup" | "sme" | "corporate" | "foreign_entity";
  name: string;
  gstin?: string;
  pan?: string;
}

export interface LedgerEntry {
  id: string;
  clientId: string;
  accountCode: string;
  transactionDate: string;
  transactionType: "debit" | "credit";
  amount: number;
  description: string;
  gstin?: string;
  hsnCode?: string;
  reconciliationStatus: string;
}

export interface TaxFiling {
  id: string;
  clientId: string;
  filingType: string;
  periodStart: string;
  periodEnd: string;
  status: string;
  dueDate: string;
}

export interface Document {
  id: string;
  clientId: string;
  fileName: string;
  docType: string;
  ocrStatus: string;
  uploadedAt: string;
}
