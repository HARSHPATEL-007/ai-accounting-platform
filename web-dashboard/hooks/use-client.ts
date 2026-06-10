import { useQuery } from "@tanstack/react-query";
import axios from "axios";
import { Client } from "@/types";

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "https://api.accounting-platform.in",
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("auth_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export function useClient(clientId: string) {
  return useQuery({
    queryKey: ["client", clientId],
    queryFn: async () => {
      const { data } = await api.get<Client>(`/api/v1/clients/${clientId}`);
      return data;
    },
  });
}

export function useLedgerEntries(clientId: string, limit = 50) {
  return useQuery({
    queryKey: ["ledger", clientId, limit],
    queryFn: async () => {
      const { data } = await api.get(`/api/v1/ledger/${clientId}?limit=${limit}`);
      return data;
    },
  });
}

export function useTaxFilings(clientId: string) {
  return useQuery({
    queryKey: ["tax-filings", clientId],
    queryFn: async () => {
      const { data } = await api.get(`/api/v1/tax-filings/${clientId}`);
      return data;
    },
  });
}

export { api };
