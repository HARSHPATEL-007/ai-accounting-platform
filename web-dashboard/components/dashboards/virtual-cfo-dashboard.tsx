"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
} from "recharts";

const runwayData = [
  { month: "Jan", cash: 5000000, burn: 1200000 },
  { month: "Feb", cash: 4800000, burn: 1250000 },
  { month: "Mar", cash: 4500000, burn: 1300000 },
  { month: "Apr", cash: 4200000, burn: 1350000 },
  { month: "May", cash: 3800000, burn: 1400000 },
  { month: "Jun", cash: 3500000, burn: 1450000 },
  { month: "Jul", cash: 3200000, burn: 1500000 },
  { month: "Aug", cash: 2800000, burn: 1550000 },
  { month: "Sep", cash: 2400000, burn: 1600000 },
  { month: "Oct", cash: 2000000, burn: 1650000 },
];

const esopData = [
  { month: "Jan", granted: 1000, vested: 0, exercised: 0 },
  { month: "Feb", granted: 1000, vested: 250, exercised: 0 },
  { month: "Mar", granted: 1000, vested: 250, exercised: 100 },
  { month: "Apr", granted: 1500, vested: 500, exercised: 200 },
  { month: "May", granted: 1500, vested: 750, exercised: 300 },
  { month: "Jun", granted: 2000, vested: 1000, exercised: 400 },
];

export function VirtualCFODashboard() {
  const currentCash = 3200000;
  const monthlyBurn = 1500000;
  const runwayMonths = Math.floor(currentCash / monthlyBurn);

  return (
    <div className="space-y-6">
      {/* Runway Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-500">Cash Balance</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">₹{(currentCash / 100000).toFixed(2)}L</p>
            <Badge variant="outline" className="mt-2">Updated today</Badge>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-500">Monthly Burn Rate</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">₹{(monthlyBurn / 100000).toFixed(2)}L</p>
            <Badge variant="destructive" className="mt-2">+8% vs last month</Badge>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-500">Runway</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{runwayMonths} months</p>
            <Badge variant={runwayMonths < 6 ? "destructive" : "default"} className="mt-2">
              {runwayMonths < 6 ? "Critical" : "Healthy"}
            </Badge>
          </CardContent>
        </Card>
      </div>

      {/* Cash Flow Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Cash Runway Projection</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[400px]">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={runwayData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis tickFormatter={(value) => `₹${(value / 100000).toFixed(0)}L`} />
                <Tooltip formatter={(value: number) => `₹${(value / 100000).toFixed(2)}L`} />
                <Area
                  type="monotone"
                  dataKey="cash"
                  stroke="#2563eb"
                  fill="#3b82f6"
                  fillOpacity={0.3}
                  name="Cash Balance"
                />
                <Area
                  type="monotone"
                  dataKey="burn"
                  stroke="#dc2626"
                  fill="#ef4444"
                  fillOpacity={0.3}
                  name="Monthly Burn"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* ESOP Cap Table */}
      <Card>
        <CardHeader>
          <CardTitle>ESOP Cap Table</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={esopData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip />
                <Line type="monotone" dataKey="granted" stroke="#2563eb" name="Granted" />
                <Line type="monotone" dataKey="vested" stroke="#16a34a" name="Vested" />
                <Line type="monotone" dataKey="exercised" stroke="#dc2626" name="Exercised" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
