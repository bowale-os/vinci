import clsx from "clsx";

export function Skeleton({ className }: { className?: string }) {
  return <div className={clsx("skeleton rounded-lg", className)} />;
}

export function SkeletonCard() {
  return (
    <div className="bg-white border border-[rgba(15,31,61,0.06)] rounded-[16px] p-8 space-y-4"
      style={{ boxShadow: "0 2px 8px rgba(15,31,61,0.06)" }}>
      <Skeleton className="h-5 w-2/3" />
      <Skeleton className="h-4 w-full" />
      <Skeleton className="h-4 w-5/6" />
      <Skeleton className="h-4 w-3/4" />
    </div>
  );
}
