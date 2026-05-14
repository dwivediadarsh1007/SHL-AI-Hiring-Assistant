import React from "react";
import { ExternalLink, Award } from "lucide-react";
import { AssessmentRecommendation } from "../../types/api";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "../ui/card";
import { Button } from "../ui/button";

interface RecommendationCardProps {
  assessment: AssessmentRecommendation;
}

export function RecommendationCard({ assessment }: RecommendationCardProps) {
  return (
    <Card className="w-full overflow-hidden transition-all hover:border-blue-200 hover:shadow-md">
      <CardHeader className="bg-slate-50 pb-4">
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <CardTitle className="text-base text-slate-900">{assessment.name}</CardTitle>
            <div className="inline-flex items-center rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-semibold text-blue-800">
              {assessment.test_type}
            </div>
          </div>
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-indigo-100 text-indigo-600">
            <Award size={18} />
          </div>
        </div>
      </CardHeader>
      <CardContent className="pt-4">
        <p className="text-sm text-slate-600">
          This assessment evaluates candidates for core competencies related to {assessment.test_type.toLowerCase()} and is validated against SHL's global talent framework.
        </p>
      </CardContent>
      <CardFooter className="border-t border-slate-100 bg-slate-50/50 py-3">
        <a href={assessment.url} target="_blank" rel="noopener noreferrer" className="w-full">
          <Button variant="outline" className="w-full gap-2 text-blue-600 hover:text-blue-700">
            View on SHL Catalog
            <ExternalLink size={14} />
          </Button>
        </a>
      </CardFooter>
    </Card>
  );
}
