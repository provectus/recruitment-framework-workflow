import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/shared/ui/card";

const INTERVIEWS = [
  { candidate: "Chen Wei", position: "Data Engineer", date: "Feb 11, 2026 · 10:00 AM", interviewer: "Anna K." },
  { candidate: "Sam Patel", position: "Platform Engineer", date: "Feb 11, 2026 · 2:00 PM", interviewer: "Dmitry S." },
  { candidate: "Lena Ivanova", position: "QA Engineer", date: "Feb 12, 2026 · 11:00 AM", interviewer: "Mark T." },
  { candidate: "Omar Hassan", position: "Backend Engineer", date: "Feb 13, 2026 · 3:30 PM", interviewer: "Julia R." },
] as const;

export function UpcomingInterviews() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Upcoming Interviews</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {INTERVIEWS.map((interview) => (
          <div key={interview.candidate} className="flex items-start justify-between gap-2">
            <div className="min-w-0">
              <p className="text-sm font-medium truncate">{interview.candidate}</p>
              <p className="text-xs text-muted-foreground truncate">{interview.position}</p>
            </div>
            <div className="text-right shrink-0">
              <p className="text-xs">{interview.date}</p>
              <p className="text-xs text-muted-foreground">{interview.interviewer}</p>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
