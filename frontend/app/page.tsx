import React from "react";
import Link from "next/link";
import { ArrowRight, BrainCircuit, LayoutList, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function Home() {
  return (
    <div className="flex min-h-full flex-col bg-slate-50">
      <main className="flex-1">
        <section className="px-6 py-24 md:py-32 lg:px-8">
          <div className="mx-auto max-w-3xl text-center">
            <h1 className="text-4xl font-extrabold tracking-tight text-slate-900 sm:text-6xl">
              Hire smarter with the <span className="text-blue-600">SHL AI Assistant</span>
            </h1>
            <p className="mt-6 text-lg leading-8 text-slate-600">
              Stop guessing which assessments to use. Simply describe the role you are hiring for, and our AI will recommend the perfectly matched SHL catalog assessments instantly.
            </p>
            <div className="mt-10 flex items-center justify-center gap-x-6">
              <Link href="/chat">
                <Button size="lg" className="gap-2 rounded-full px-8">
                  Start Hiring
                  <ArrowRight size={18} />
                </Button>
              </Link>
            </div>
          </div>
        </section>

        <section className="mx-auto max-w-7xl px-6 lg:px-8 py-16">
          <div className="mx-auto grid max-w-2xl grid-cols-1 gap-8 lg:max-w-none lg:grid-cols-3">
            <div className="flex flex-col items-center text-center rounded-2xl bg-white p-8 shadow-sm ring-1 ring-slate-200">
              <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-blue-100 text-blue-600">
                <BrainCircuit size={24} />
              </div>
              <h3 className="text-lg font-semibold text-slate-900">Conversational AI</h3>
              <p className="mt-2 text-sm text-slate-500">
                Chat naturally. The assistant asks clarifying questions if your requirements are vague, ensuring highly accurate recommendations.
              </p>
            </div>
            
            <div className="flex flex-col items-center text-center rounded-2xl bg-white p-8 shadow-sm ring-1 ring-slate-200">
              <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-emerald-100 text-emerald-600">
                <LayoutList size={24} />
              </div>
              <h3 className="text-lg font-semibold text-slate-900">Full Catalog Access</h3>
              <p className="mt-2 text-sm text-slate-500">
                Grounded entirely in SHL's official catalog. View details, durations, and direct links to the official assessment pages.
              </p>
            </div>
            
            <div className="flex flex-col items-center text-center rounded-2xl bg-white p-8 shadow-sm ring-1 ring-slate-200">
              <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-indigo-100 text-indigo-600">
                <ShieldCheck size={24} />
              </div>
              <h3 className="text-lg font-semibold text-slate-900">Enterprise Guardrails</h3>
              <p className="mt-2 text-sm text-slate-500">
                Built with multi-layered safety guardrails to prevent hallucinations, ensuring 100% accurate, recruiter-defensible output.
              </p>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
