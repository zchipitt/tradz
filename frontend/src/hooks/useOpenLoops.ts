/**
 * React Query hooks for Open Loops data.
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getOpenLoops,
  getOpenLoopById,
  createOpenLoop,
  updateOpenLoop,
  deleteOpenLoop,
} from '../api/client';
import type {
  OpenLoopsListResponse,
  OpenLoopDetail,
  OpenLoopAPIItem,
  CreateOpenLoopRequest,
  UpdateOpenLoopRequest,
  OpenLoopStatusValue,
} from '../api/types';

export const OPEN_LOOPS_QUERY_KEY = ['openLoops'];

/**
 * Hook to fetch all open loops with optional status filter.
 */
export function useOpenLoops(
  status: OpenLoopStatusValue | 'all' = 'all',
  enabled = true
) {
  return useQuery<OpenLoopsListResponse>({
    queryKey: [...OPEN_LOOPS_QUERY_KEY, status],
    queryFn: () => getOpenLoops(status),
    enabled,
    staleTime: 2 * 60 * 1000, // 2 minutes
    refetchInterval: 5 * 60 * 1000, // Auto-refresh every 5 minutes
  });
}

export const OPEN_LOOP_DETAIL_KEY = (loopId: string) => ['openLoops', loopId];

/**
 * Hook to fetch a single open loop by ID.
 */
export function useOpenLoopDetail(loopId: string | undefined, enabled = true) {
  return useQuery<OpenLoopDetail>({
    queryKey: OPEN_LOOP_DETAIL_KEY(loopId ?? ''),
    queryFn: () => getOpenLoopById(loopId!),
    enabled: enabled && !!loopId,
    staleTime: 2 * 60 * 1000, // 2 minutes
    retry: (failureCount, error) => {
      // Don't retry on 404 errors
      if (error instanceof Error && error.message.includes('404')) {
        return false;
      }
      return failureCount < 2;
    },
  });
}

/**
 * Hook to create a new open loop.
 */
export function useCreateOpenLoop() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: CreateOpenLoopRequest) => createOpenLoop(request),
    onSuccess: () => {
      // Invalidate all open loops queries to refresh the list
      queryClient.invalidateQueries({ queryKey: OPEN_LOOPS_QUERY_KEY });
    },
  });
}

/**
 * Hook to update an open loop (status and/or progress note).
 */
export function useUpdateOpenLoop() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      loopId,
      request,
    }: {
      loopId: string;
      request: UpdateOpenLoopRequest;
    }) => updateOpenLoop(loopId, request),

    // Optimistic update
    onMutate: async ({ loopId, request }) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: OPEN_LOOPS_QUERY_KEY });

      // Snapshot current data for rollback
      const previousLists = queryClient.getQueriesData<OpenLoopsListResponse>({
        queryKey: OPEN_LOOPS_QUERY_KEY,
      });

      // Optimistically update all matching queries
      queryClient.setQueriesData<OpenLoopsListResponse>(
        { queryKey: OPEN_LOOPS_QUERY_KEY },
        (old) => {
          if (!old) return old;
          return {
            ...old,
            loops: old.loops.map((loop: OpenLoopAPIItem) => {
              if (loop.loop_id !== loopId) return loop;
              return {
                ...loop,
                ...(request.status && { status: request.status }),
                ...(request.progress_note && {
                  progress_notes_count: loop.progress_notes_count + 1,
                }),
                ...(request.status === 'resolved' && {
                  resolved_at: new Date().toISOString(),
                }),
              };
            }),
          };
        }
      );

      return { previousLists };
    },

    // On error, rollback to previous data
    onError: (_err, _vars, context) => {
      if (context?.previousLists) {
        context.previousLists.forEach(([queryKey, data]) => {
          queryClient.setQueryData(queryKey, data);
        });
      }
    },

    // Always refetch after mutation settles
    onSettled: (_data, _error, { loopId }) => {
      queryClient.invalidateQueries({ queryKey: OPEN_LOOPS_QUERY_KEY });
      queryClient.invalidateQueries({ queryKey: OPEN_LOOP_DETAIL_KEY(loopId) });
    },
  });
}

/**
 * Hook to delete an open loop.
 */
export function useDeleteOpenLoop() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (loopId: string) => deleteOpenLoop(loopId),

    // Optimistic update - remove from list immediately
    onMutate: async (loopId) => {
      await queryClient.cancelQueries({ queryKey: OPEN_LOOPS_QUERY_KEY });

      const previousLists = queryClient.getQueriesData<OpenLoopsListResponse>({
        queryKey: OPEN_LOOPS_QUERY_KEY,
      });

      queryClient.setQueriesData<OpenLoopsListResponse>(
        { queryKey: OPEN_LOOPS_QUERY_KEY },
        (old) => {
          if (!old) return old;
          return {
            ...old,
            loops: old.loops.filter(
              (loop: OpenLoopAPIItem) => loop.loop_id !== loopId
            ),
            total_count: old.total_count - 1,
          };
        }
      );

      return { previousLists };
    },

    onError: (_err, _loopId, context) => {
      if (context?.previousLists) {
        context.previousLists.forEach(([queryKey, data]) => {
          queryClient.setQueryData(queryKey, data);
        });
      }
    },

    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: OPEN_LOOPS_QUERY_KEY });
    },
  });
}

/**
 * Convenience hook that provides all open loop mutation actions.
 */
export function useOpenLoopActions() {
  const createMutation = useCreateOpenLoop();
  const updateMutation = useUpdateOpenLoop();
  const deleteMutation = useDeleteOpenLoop();

  return {
    // Create a new loop
    create: (question: string, eventId?: string) =>
      createMutation.mutateAsync({ question, event_id: eventId }),

    // Mark loop as resolved
    resolve: (loopId: string) =>
      updateMutation.mutateAsync({
        loopId,
        request: { status: 'resolved' },
      }),

    // Mark loop as in progress
    startProgress: (loopId: string) =>
      updateMutation.mutateAsync({
        loopId,
        request: { status: 'in_progress' },
      }),

    // Add a progress note
    addNote: (loopId: string, note: string) =>
      updateMutation.mutateAsync({
        loopId,
        request: { progress_note: note },
      }),

    // Update status and add note together
    updateWithNote: (
      loopId: string,
      status: OpenLoopStatusValue,
      note: string
    ) =>
      updateMutation.mutateAsync({
        loopId,
        request: { status, progress_note: note },
      }),

    // Delete a loop
    delete: (loopId: string) => deleteMutation.mutateAsync(loopId),

    // Mutation states
    isCreating: createMutation.isPending,
    isUpdating: updateMutation.isPending,
    isDeleting: deleteMutation.isPending,
    isLoading:
      createMutation.isPending ||
      updateMutation.isPending ||
      deleteMutation.isPending,
  };
}
