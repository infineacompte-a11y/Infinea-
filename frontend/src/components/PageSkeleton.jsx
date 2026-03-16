import { Skeleton } from "@/components/ui/skeleton";
import { Card, CardContent } from "@/components/ui/card";

/**
 * Reusable skeleton loaders for page loading states.
 * Replaces generic spinners with layout-aware placeholders.
 *
 * Variants:
 * - cards: Grid of card skeletons (Objectives, Routines, Groups)
 * - list: Stacked list items (MyDay, Actions)
 * - dashboard: Mixed layout (Dashboard)
 */

function CardSkeleton() {
  return (
    <Card>
      <CardContent className="p-5">
        <div className="flex items-start gap-3">
          <Skeleton className="w-10 h-10 rounded-xl shrink-0" />
          <div className="flex-1 space-y-2">
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-3 w-1/2" />
          </div>
        </div>
        <div className="mt-4 space-y-2">
          <Skeleton className="h-2 w-full rounded-full" />
          <div className="flex justify-between">
            <Skeleton className="h-3 w-16" />
            <Skeleton className="h-3 w-12" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function ListItemSkeleton() {
  return (
    <div className="flex items-center gap-3 p-4 rounded-lg border border-border/50">
      <Skeleton className="w-8 h-8 rounded-lg shrink-0" />
      <div className="flex-1 space-y-2">
        <Skeleton className="h-4 w-2/3" />
        <Skeleton className="h-3 w-1/3" />
      </div>
      <Skeleton className="w-20 h-8 rounded-md" />
    </div>
  );
}

export function CardsSkeleton({ count = 3 }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: count }).map((_, i) => (
        <CardSkeleton key={i} />
      ))}
    </div>
  );
}

export function ListSkeleton({ count = 4 }) {
  return (
    <div className="space-y-2">
      {Array.from({ length: count }).map((_, i) => (
        <ListItemSkeleton key={i} />
      ))}
    </div>
  );
}

export function DashboardSkeleton() {
  return (
    <div className="space-y-4">
      {/* Stats row */}
      <div className="grid grid-cols-2 gap-3">
        <Card>
          <CardContent className="p-4">
            <Skeleton className="h-3 w-20 mb-2" />
            <Skeleton className="h-7 w-12" />
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <Skeleton className="h-3 w-20 mb-2" />
            <Skeleton className="h-7 w-12" />
          </CardContent>
        </Card>
      </div>
      {/* Action cards */}
      <CardsSkeleton count={2} />
    </div>
  );
}

export function MyDaySkeleton() {
  return (
    <div className="space-y-4">
      {/* Greeting skeleton */}
      <div className="space-y-2 mb-6">
        <Skeleton className="h-6 w-48" />
        <Skeleton className="h-4 w-32" />
      </div>
      {/* Sections */}
      <ListSkeleton count={3} />
      <CardsSkeleton count={2} />
    </div>
  );
}
