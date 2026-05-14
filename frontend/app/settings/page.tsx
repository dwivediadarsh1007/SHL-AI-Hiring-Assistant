"use client";

import React, { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { chatAPI } from "@/lib/api";

export default function SettingsPage() {
  const [apiUrl, setApiUrl] = useState("");
  const [healthStatus, setHealthStatus] = useState<"checking" | "ok" | "error" | "idle">("idle");

  useEffect(() => {
    // Usually environment variables are fixed at build time in Next.js
    // but for this demo settings page we can display the current configured url
    setApiUrl(process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000");
  }, []);

  const checkConnection = async () => {
    setHealthStatus("checking");
    try {
      const res = await chatAPI.checkHealth();
      if (res.status === "ok") {
        setHealthStatus("ok");
      } else {
        setHealthStatus("error");
      }
    } catch (e) {
      setHealthStatus("error");
    }
  };

  return (
    <div className="p-8 max-w-4xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight text-slate-900">Settings</h1>
        <p className="text-slate-500">Manage your application settings and connections.</p>
      </div>

      <div className="grid gap-6">
        <Card>
          <CardHeader>
            <CardTitle>API Configuration</CardTitle>
            <CardDescription>
              Configure the connection to your SHL FastAPI Backend.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label htmlFor="apiUrl" className="text-sm font-medium leading-none text-slate-700">
                Backend API URL
              </label>
              <Input
                id="apiUrl"
                value={apiUrl}
                readOnly
                className="bg-slate-50"
              />
              <p className="text-[0.8rem] text-slate-500">
                To change this, update your <code className="bg-slate-100 px-1 rounded">.env.local</code> file and restart the frontend server.
              </p>
            </div>
          </CardContent>
          <CardFooter className="flex justify-between border-t border-slate-100 bg-slate-50 pt-6">
            <div className="flex items-center gap-2">
              <Button variant="outline" onClick={checkConnection}>
                Test Connection
              </Button>
              {healthStatus === "checking" && <span className="text-sm text-blue-600">Checking...</span>}
              {healthStatus === "ok" && <span className="text-sm text-emerald-600 font-medium">Connection Successful</span>}
              {healthStatus === "error" && <span className="text-sm text-red-600 font-medium">Connection Failed</span>}
            </div>
          </CardFooter>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Appearance</CardTitle>
            <CardDescription>
              Customize how the SHL application looks on your device.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-4">
              <div className="flex items-center space-x-2 rounded-lg border-2 border-blue-600 p-2">
                <div className="h-4 w-4 rounded-full bg-blue-600"></div>
                <span className="text-sm font-medium">Light</span>
              </div>
              <div className="flex items-center space-x-2 rounded-lg border-2 border-transparent p-2 opacity-50 cursor-not-allowed">
                <div className="h-4 w-4 rounded-full bg-slate-900"></div>
                <span className="text-sm font-medium">Dark (Coming Soon)</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
