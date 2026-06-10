"use client";

import { useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ComplianceAutopilot } from "@/components/dashboards/compliance-autopilot";
import { VirtualCFODashboard } from "@/components/dashboards/virtual-cfo-dashboard";
import { DeepAuditConsole } from "@/components/dashboards/deep-audit-console";
import { CrossBorderNavigator } from "@/components/dashboards/cross-border-navigator";
import { ChatInterface } from "@/components/chat/chat-interface";
import { Sidebar } from "@/components/ui/sidebar";

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState("compliance");

  return (
    <div className="flex h-screen">
      <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />

      <main className="flex-1 overflow-y-auto p-6">
        <div className="mx-auto max-w-7xl">
          <header className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900">
              AI-Native Accounting Platform
            </h1>
            <p className="mt-1 text-sm text-gray-500">
              Hyper-automated accounting, tax, and compliance for Indian businesses
            </p>
          </header>

          <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
            <TabsList className="grid w-full grid-cols-4 lg:w-[600px]">
              <TabsTrigger value="compliance">Compliance</TabsTrigger>
              <TabsTrigger value="vCFO">Virtual CFO</TabsTrigger>
              <TabsTrigger value="audit">Deep Audit</TabsTrigger>
              <TabsTrigger value="crossborder">Cross-Border</TabsTrigger>
            </TabsList>

            <TabsContent value="compliance" className="space-y-4">
              <ComplianceAutopilot />
            </TabsContent>

            <TabsContent value="vCFO" className="space-y-4">
              <VirtualCFODashboard />
            </TabsContent>

            <TabsContent value="audit" className="space-y-4">
              <DeepAuditConsole />
            </TabsContent>

            <TabsContent value="crossborder" className="space-y-4">
              <CrossBorderNavigator />
            </TabsContent>
          </Tabs>
        </div>

        {/* Floating Chat */}
        <ChatInterface />
      </main>
    </div>
  );
}
