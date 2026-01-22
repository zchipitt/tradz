/**
 * React Query hooks for Quality Gate Settings API interactions (US-025b).
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getQualityGateSettings,
  updateQualityGateSettings,
  resetQualityGateSettings,
} from '../api/client';
import type {
  QualityGateSettingsResponse,
  UpdateQualityGateSettingsRequest,
  UpdateQualityGateSettingsResponse,
  QualityGateSettings,
} from '../api/types';

// Query keys
export const QUALITY_GATE_SETTINGS_KEY = ['settings', 'quality-gates'];

/**
 * Hook to fetch quality gate settings.
 * Data is cached for 5 minutes and auto-refreshes every 5 minutes.
 */
export function useQualityGateSettings(enabled = true) {
  return useQuery<QualityGateSettingsResponse>({
    queryKey: QUALITY_GATE_SETTINGS_KEY,
    queryFn: getQualityGateSettings,
    enabled,
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 2,
  });
}

/**
 * Hook to update quality gate settings.
 * Supports partial updates - only provided fields are updated.
 */
export function useUpdateQualityGateSettings() {
  const queryClient = useQueryClient();

  return useMutation<
    UpdateQualityGateSettingsResponse,
    Error,
    UpdateQualityGateSettingsRequest,
    { previousData: QualityGateSettingsResponse | undefined }
  >({
    mutationFn: updateQualityGateSettings,

    // Optimistic update
    onMutate: async (newSettings) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: QUALITY_GATE_SETTINGS_KEY });

      // Snapshot current data for rollback
      const previousData = queryClient.getQueryData<QualityGateSettingsResponse>(
        QUALITY_GATE_SETTINGS_KEY
      );

      // Optimistically update the cache
      if (previousData) {
        queryClient.setQueryData<QualityGateSettingsResponse>(
          QUALITY_GATE_SETTINGS_KEY,
          {
            ...previousData,
            settings: {
              ...previousData.settings,
              ...(newSettings.min_confidence !== undefined && {
                min_confidence: newSettings.min_confidence,
              }),
              ...(newSettings.min_sources !== undefined && {
                min_sources: newSettings.min_sources,
              }),
              ...(newSettings.min_anomaly !== undefined && {
                min_anomaly: newSettings.min_anomaly,
              }),
              ...(newSettings.min_catalyst !== undefined && {
                min_catalyst: newSettings.min_catalyst,
              }),
              ...(newSettings.require_invalidation !== undefined && {
                require_invalidation: newSettings.require_invalidation,
              }),
            },
          }
        );
      }

      return { previousData };
    },

    // On error, rollback to previous data
    onError: (_err, _vars, context) => {
      if (context?.previousData) {
        queryClient.setQueryData(QUALITY_GATE_SETTINGS_KEY, context.previousData);
      }
    },

    // Always refetch after mutation settles
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: QUALITY_GATE_SETTINGS_KEY });
    },
  });
}

/**
 * Hook to reset quality gate settings to defaults.
 */
export function useResetQualityGateSettings() {
  const queryClient = useQueryClient();

  return useMutation<UpdateQualityGateSettingsResponse, Error, void>({
    mutationFn: resetQualityGateSettings,

    // On success, update the cache with the response (which contains defaults)
    onSuccess: (data) => {
      queryClient.setQueryData<QualityGateSettingsResponse>(
        QUALITY_GATE_SETTINGS_KEY,
        (old) => {
          if (!old) return undefined;
          return {
            ...old,
            settings: data.settings,
          };
        }
      );
    },

    // Always refetch after mutation settles
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: QUALITY_GATE_SETTINGS_KEY });
    },
  });
}

/**
 * Helper function to evaluate a sample event against quality gate settings.
 * This is a client-side preview - the actual evaluation happens on the backend.
 */
export function evaluateSampleEvent(
  settings: QualityGateSettings,
  sampleEvent: {
    confidence_score: number;
    anomaly_score: number;
    catalyst_score: number;
    source_count: number;
    has_invalidation: boolean;
  }
): {
  passed: boolean;
  gate_score: number;
  results: {
    name: string;
    passed: boolean;
    actual: number | boolean;
    threshold: number | boolean;
  }[];
} {
  const results = [
    {
      name: 'Confidence',
      passed: sampleEvent.confidence_score >= settings.min_confidence,
      actual: sampleEvent.confidence_score,
      threshold: settings.min_confidence,
    },
    {
      name: 'Anomaly',
      passed: sampleEvent.anomaly_score >= settings.min_anomaly,
      actual: sampleEvent.anomaly_score,
      threshold: settings.min_anomaly,
    },
    {
      name: 'Catalyst',
      passed: sampleEvent.catalyst_score >= settings.min_catalyst,
      actual: sampleEvent.catalyst_score,
      threshold: settings.min_catalyst,
    },
    {
      name: 'Sources',
      passed: sampleEvent.source_count >= settings.min_sources,
      actual: sampleEvent.source_count,
      threshold: settings.min_sources,
    },
    {
      name: 'Invalidation',
      passed: !settings.require_invalidation || sampleEvent.has_invalidation,
      actual: sampleEvent.has_invalidation,
      threshold: settings.require_invalidation,
    },
  ];

  const passedCount = results.filter((r) => r.passed).length;
  const gate_score = Math.round((passedCount / results.length) * 100);
  const passed = results.every((r) => r.passed);

  return { passed, gate_score, results };
}

/**
 * Convenience hook that provides all quality gate settings actions.
 */
export function useQualityGateSettingsActions() {
  const updateMutation = useUpdateQualityGateSettings();
  const resetMutation = useResetQualityGateSettings();

  return {
    // Update settings
    update: (settings: UpdateQualityGateSettingsRequest) =>
      updateMutation.mutateAsync(settings),

    // Reset to defaults
    reset: () => resetMutation.mutateAsync(),

    // Mutation states
    isUpdating: updateMutation.isPending,
    isResetting: resetMutation.isPending,
    isLoading: updateMutation.isPending || resetMutation.isPending,

    // Error states
    updateError: updateMutation.error,
    resetError: resetMutation.error,
  };
}
