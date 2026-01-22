/**
 * Settings page - Configure quality gate thresholds (US-025b).
 * Brutalist design aesthetic - black/white + yellow accent.
 */
import { useState, useEffect, useMemo } from 'react';
import {
  Settings as SettingsIcon,
  RotateCcw,
  Save,
  AlertCircle,
  CheckCircle,
  XCircle,
  Activity,
  TrendingUp,
  Zap,
  Shield,
  Users,
} from 'lucide-react';
import { cn } from '../lib/utils';
import { Button } from '../components/common/Button';
import {
  useQualityGateSettings,
  useQualityGateSettingsActions,
  evaluateSampleEvent,
} from '../hooks/useQualityGateSettings';
import type { QualityGateSettings } from '../api/types';

// Sample event for preview
const DEFAULT_SAMPLE_EVENT = {
  confidence_score: 65,
  anomaly_score: 55,
  catalyst_score: 45,
  source_count: 3,
  has_invalidation: true,
};

interface SliderInputProps {
  label: string;
  description: string;
  value: number;
  defaultValue: number;
  onChange: (value: number) => void;
  min: number;
  max: number;
  step?: number;
  unit?: string;
  icon: React.ReactNode;
}

function SliderInput({
  label,
  description,
  value,
  defaultValue,
  onChange,
  min,
  max,
  step = 1,
  unit = '',
  icon,
}: SliderInputProps) {
  const isModified = value !== defaultValue;
  const percentage = ((value - min) / (max - min)) * 100;

  return (
    <div className="p-4 border-2 border-gray-300 hover:border-black transition-colors">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className="p-1.5 border-2 border-black bg-gray-100">{icon}</div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-sm uppercase tracking-wide">{label}</span>
              {isModified && (
                <span className="px-1.5 py-0.5 text-[10px] font-bold bg-primary border border-black">
                  MODIFIED
                </span>
              )}
            </div>
            <p className="text-xs text-gray-500 mt-0.5">{description}</p>
          </div>
        </div>
        <div className="text-right">
          <div className="text-lg font-bold tabular-nums">
            {value}
            {unit}
          </div>
          <div className="text-xs text-gray-500">
            Default: {defaultValue}
            {unit}
          </div>
        </div>
      </div>

      {/* Slider track */}
      <div className="relative mt-2">
        <div className="h-2 bg-gray-200 border border-gray-400">
          <div
            className="h-full bg-black transition-all"
            style={{ width: `${percentage}%` }}
          />
        </div>
        <input
          type="range"
          min={min}
          max={max}
          step={step}
          value={value}
          onChange={(e) => onChange(Number(e.target.value))}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
        />
        {/* Tick marks */}
        <div className="flex justify-between mt-1 text-[10px] text-gray-400">
          <span>{min}{unit}</span>
          <span>{Math.round((max - min) / 2 + min)}{unit}</span>
          <span>{max}{unit}</span>
        </div>
      </div>
    </div>
  );
}

interface ToggleInputProps {
  label: string;
  description: string;
  value: boolean;
  defaultValue: boolean;
  onChange: (value: boolean) => void;
  icon: React.ReactNode;
}

function ToggleInput({
  label,
  description,
  value,
  defaultValue,
  onChange,
  icon,
}: ToggleInputProps) {
  const isModified = value !== defaultValue;

  return (
    <div className="p-4 border-2 border-gray-300 hover:border-black transition-colors">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2">
          <div className="p-1.5 border-2 border-black bg-gray-100">{icon}</div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-sm uppercase tracking-wide">{label}</span>
              {isModified && (
                <span className="px-1.5 py-0.5 text-[10px] font-bold bg-primary border border-black">
                  MODIFIED
                </span>
              )}
            </div>
            <p className="text-xs text-gray-500 mt-0.5">{description}</p>
          </div>
        </div>
        <button
          onClick={() => onChange(!value)}
          className={cn(
            'relative w-12 h-6 border-2 border-black transition-colors cursor-pointer',
            value ? 'bg-primary' : 'bg-gray-200'
          )}
        >
          <div
            className={cn(
              'absolute top-0.5 w-4 h-4 bg-black transition-transform',
              value ? 'left-6' : 'left-0.5'
            )}
          />
        </button>
      </div>
      <div className="mt-2 text-right">
        <span className={cn('text-sm font-bold', value ? 'text-black' : 'text-gray-500')}>
          {value ? 'REQUIRED' : 'OPTIONAL'}
        </span>
        <span className="text-xs text-gray-500 ml-2">
          (Default: {defaultValue ? 'Required' : 'Optional'})
        </span>
      </div>
    </div>
  );
}

interface PreviewGateResultProps {
  name: string;
  passed: boolean;
  actual: number | boolean;
  threshold: number | boolean;
}

function PreviewGateResult({ name, passed, actual, threshold }: PreviewGateResultProps) {
  return (
    <div
      className={cn(
        'flex items-center justify-between p-2 border-2',
        passed ? 'border-green-500 bg-green-50' : 'border-red-500 bg-red-50'
      )}
    >
      <div className="flex items-center gap-2">
        {passed ? (
          <CheckCircle size={14} className="text-green-600" />
        ) : (
          <XCircle size={14} className="text-red-600" />
        )}
        <span className="text-xs font-bold uppercase">{name}</span>
      </div>
      <div className="text-xs text-gray-600">
        {typeof actual === 'boolean' ? (actual ? 'Yes' : 'No') : actual} /{' '}
        {typeof threshold === 'boolean' ? (threshold ? 'Required' : 'Optional') : threshold}
      </div>
    </div>
  );
}

export function Settings() {
  // Fetch current settings
  const { data, isLoading, error, refetch } = useQualityGateSettings();
  const { update, reset, isUpdating, isLoading: isMutating } =
    useQualityGateSettingsActions();

  // Local state for form values (allows editing before save)
  const [localSettings, setLocalSettings] = useState<QualityGateSettings | null>(null);
  const [sampleEvent, setSampleEvent] = useState(DEFAULT_SAMPLE_EVENT);
  const [saveMessage, setSaveMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Initialize local settings when data loads
  useEffect(() => {
    if (data?.settings && !localSettings) {
      setLocalSettings(data.settings);
    }
  }, [data?.settings, localSettings]);

  // Clear save message after 3 seconds
  useEffect(() => {
    if (saveMessage) {
      const timer = setTimeout(() => setSaveMessage(null), 3000);
      return () => clearTimeout(timer);
    }
  }, [saveMessage]);

  // Check if there are unsaved changes
  const hasChanges = useMemo(() => {
    if (!data?.settings || !localSettings) return false;
    return (
      localSettings.min_confidence !== data.settings.min_confidence ||
      localSettings.min_sources !== data.settings.min_sources ||
      localSettings.min_anomaly !== data.settings.min_anomaly ||
      localSettings.min_catalyst !== data.settings.min_catalyst ||
      localSettings.require_invalidation !== data.settings.require_invalidation
    );
  }, [data?.settings, localSettings]);

  // Preview evaluation
  const previewResult = useMemo(() => {
    if (!localSettings) return null;
    return evaluateSampleEvent(localSettings, sampleEvent);
  }, [localSettings, sampleEvent]);

  // Handlers
  const handleSave = async () => {
    if (!localSettings) return;
    try {
      await update(localSettings);
      setSaveMessage({ type: 'success', text: 'Settings saved successfully!' });
    } catch (err) {
      setSaveMessage({ type: 'error', text: 'Failed to save settings. Please try again.' });
    }
  };

  const handleReset = async () => {
    try {
      const result = await reset();
      setLocalSettings(result.settings);
      setSaveMessage({ type: 'success', text: 'Settings reset to defaults!' });
    } catch (err) {
      setSaveMessage({ type: 'error', text: 'Failed to reset settings. Please try again.' });
    }
  };

  const handleDiscardChanges = () => {
    if (data?.settings) {
      setLocalSettings(data.settings);
    }
  };

  const updateSetting = <K extends keyof QualityGateSettings>(
    key: K,
    value: QualityGateSettings[K]
  ) => {
    if (localSettings) {
      setLocalSettings({ ...localSettings, [key]: value });
    }
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="space-y-6 font-mono">
        <div className="flex items-center gap-3">
          <SettingsIcon size={20} />
          <h1 className="text-xl font-bold">Settings</h1>
        </div>
        <div className="animate-pulse space-y-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-24 bg-gray-200 border-2 border-gray-300" />
          ))}
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="space-y-6 font-mono">
        <div className="flex items-center gap-3">
          <SettingsIcon size={20} />
          <h1 className="text-xl font-bold">Settings</h1>
        </div>
        <div className="p-6 border-2 border-red-600 bg-red-50">
          <div className="flex items-center gap-2 text-red-600 mb-2">
            <AlertCircle size={16} />
            <span className="font-bold uppercase text-sm">Error Loading Settings</span>
          </div>
          <p className="text-sm text-red-700 mb-4">{error.message}</p>
          <Button variant="danger" size="sm" onClick={() => refetch()}>
            Retry
          </Button>
        </div>
      </div>
    );
  }

  const defaults = data?.defaults;

  return (
    <div className="space-y-6 font-mono">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <SettingsIcon size={20} />
          <div>
            <h1 className="text-xl font-bold">Settings</h1>
            <p className="text-sm text-gray-600 mt-0.5">
              Configure quality gate thresholds for trade idea generation
            </p>
          </div>
        </div>
      </div>

      {/* Save message toast */}
      {saveMessage && (
        <div
          className={cn(
            'fixed top-20 right-6 z-50 p-4 border-2 shadow-brutal-sm',
            saveMessage.type === 'success'
              ? 'bg-green-50 border-green-600'
              : 'bg-red-50 border-red-600'
          )}
        >
          <div className="flex items-center gap-2">
            {saveMessage.type === 'success' ? (
              <CheckCircle size={16} className="text-green-600" />
            ) : (
              <AlertCircle size={16} className="text-red-600" />
            )}
            <span className="text-sm font-bold">{saveMessage.text}</span>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Settings Panel */}
        <div className="lg:col-span-2 space-y-4">
          {/* Quality Gates Section */}
          <div className="bg-white border-2 border-black overflow-hidden">
            <div className="px-4 py-3 bg-gray-100 border-b-2 border-black flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Shield size={16} />
                <span className="text-sm font-bold uppercase tracking-wider">
                  Quality Gate Thresholds
                </span>
              </div>
              {hasChanges && (
                <span className="px-2 py-0.5 text-xs font-bold bg-primary border border-black">
                  UNSAVED CHANGES
                </span>
              )}
            </div>

            <div className="p-4 space-y-4">
              {localSettings && defaults && (
                <>
                  <SliderInput
                    label="Minimum Confidence"
                    description="Minimum confidence score required to generate a trade idea"
                    value={localSettings.min_confidence}
                    defaultValue={defaults.min_confidence}
                    onChange={(v) => updateSetting('min_confidence', v)}
                    min={0}
                    max={100}
                    step={5}
                    unit="%"
                    icon={<Activity size={14} />}
                  />

                  <SliderInput
                    label="Minimum Anomaly"
                    description="Minimum anomaly score (price, volume, volatility deviation)"
                    value={localSettings.min_anomaly}
                    defaultValue={defaults.min_anomaly}
                    onChange={(v) => updateSetting('min_anomaly', v)}
                    min={0}
                    max={100}
                    step={5}
                    unit="%"
                    icon={<TrendingUp size={14} />}
                  />

                  <SliderInput
                    label="Minimum Catalyst"
                    description="Minimum catalyst score (news, filings, events)"
                    value={localSettings.min_catalyst}
                    defaultValue={defaults.min_catalyst}
                    onChange={(v) => updateSetting('min_catalyst', v)}
                    min={0}
                    max={100}
                    step={5}
                    unit="%"
                    icon={<Zap size={14} />}
                  />

                  <SliderInput
                    label="Minimum Sources"
                    description="Minimum number of independent data sources required"
                    value={localSettings.min_sources}
                    defaultValue={defaults.min_sources}
                    onChange={(v) => updateSetting('min_sources', v)}
                    min={1}
                    max={10}
                    step={1}
                    icon={<Users size={14} />}
                  />

                  <ToggleInput
                    label="Require Invalidation"
                    description="Whether an invalidation condition must be definable for trade ideas"
                    value={localSettings.require_invalidation}
                    defaultValue={defaults.require_invalidation}
                    onChange={(v) => updateSetting('require_invalidation', v)}
                    icon={<Shield size={14} />}
                  />
                </>
              )}
            </div>

            {/* Action buttons */}
            <div className="px-4 py-3 bg-gray-50 border-t-2 border-black flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={handleReset}
                  disabled={isMutating}
                  leftIcon={<RotateCcw size={14} />}
                >
                  Reset to Defaults
                </Button>
                {hasChanges && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleDiscardChanges}
                    disabled={isMutating}
                  >
                    Discard Changes
                  </Button>
                )}
              </div>
              <Button
                variant="primary"
                size="sm"
                onClick={handleSave}
                disabled={!hasChanges || isMutating}
                leftIcon={<Save size={14} />}
              >
                {isUpdating ? 'Saving...' : 'Save Changes'}
              </Button>
            </div>
          </div>
        </div>

        {/* Preview Panel */}
        <div className="space-y-4">
          <div className="bg-white border-2 border-black overflow-hidden">
            <div className="px-4 py-3 bg-gray-100 border-b-2 border-black">
              <span className="text-sm font-bold uppercase tracking-wider">
                Preview Evaluation
              </span>
            </div>

            <div className="p-4 space-y-4">
              {/* Sample Event Sliders */}
              <div className="space-y-3">
                <div className="text-xs font-bold uppercase tracking-wider text-gray-500">
                  Sample Event Values
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span>Confidence</span>
                    <span className="font-bold">{sampleEvent.confidence_score}</span>
                  </div>
                  <input
                    type="range"
                    min={0}
                    max={100}
                    value={sampleEvent.confidence_score}
                    onChange={(e) =>
                      setSampleEvent((s) => ({
                        ...s,
                        confidence_score: Number(e.target.value),
                      }))
                    }
                    className="w-full h-1 bg-gray-200 cursor-pointer"
                  />
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span>Anomaly</span>
                    <span className="font-bold">{sampleEvent.anomaly_score}</span>
                  </div>
                  <input
                    type="range"
                    min={0}
                    max={100}
                    value={sampleEvent.anomaly_score}
                    onChange={(e) =>
                      setSampleEvent((s) => ({
                        ...s,
                        anomaly_score: Number(e.target.value),
                      }))
                    }
                    className="w-full h-1 bg-gray-200 cursor-pointer"
                  />
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span>Catalyst</span>
                    <span className="font-bold">{sampleEvent.catalyst_score}</span>
                  </div>
                  <input
                    type="range"
                    min={0}
                    max={100}
                    value={sampleEvent.catalyst_score}
                    onChange={(e) =>
                      setSampleEvent((s) => ({
                        ...s,
                        catalyst_score: Number(e.target.value),
                      }))
                    }
                    className="w-full h-1 bg-gray-200 cursor-pointer"
                  />
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span>Sources</span>
                    <span className="font-bold">{sampleEvent.source_count}</span>
                  </div>
                  <input
                    type="range"
                    min={1}
                    max={10}
                    value={sampleEvent.source_count}
                    onChange={(e) =>
                      setSampleEvent((s) => ({
                        ...s,
                        source_count: Number(e.target.value),
                      }))
                    }
                    className="w-full h-1 bg-gray-200 cursor-pointer"
                  />
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-xs">Has Invalidation</span>
                  <button
                    onClick={() =>
                      setSampleEvent((s) => ({
                        ...s,
                        has_invalidation: !s.has_invalidation,
                      }))
                    }
                    className={cn(
                      'relative w-10 h-5 border-2 border-black transition-colors cursor-pointer',
                      sampleEvent.has_invalidation ? 'bg-primary' : 'bg-gray-200'
                    )}
                  >
                    <div
                      className={cn(
                        'absolute top-0 w-3.5 h-3.5 bg-black transition-transform',
                        sampleEvent.has_invalidation ? 'left-4.5' : 'left-0.5'
                      )}
                      style={{ top: '1px', left: sampleEvent.has_invalidation ? '18px' : '2px' }}
                    />
                  </button>
                </div>
              </div>

              {/* Evaluation Results */}
              {previewResult && (
                <div className="pt-4 border-t-2 border-gray-200 space-y-3">
                  <div className="text-xs font-bold uppercase tracking-wider text-gray-500">
                    Gate Evaluation
                  </div>

                  {/* Overall result */}
                  <div
                    className={cn(
                      'p-3 border-2 text-center',
                      previewResult.passed
                        ? 'border-green-600 bg-green-50'
                        : 'border-red-600 bg-red-50'
                    )}
                  >
                    <div className="flex items-center justify-center gap-2 mb-1">
                      {previewResult.passed ? (
                        <CheckCircle size={16} className="text-green-600" />
                      ) : (
                        <XCircle size={16} className="text-red-600" />
                      )}
                      <span className="font-bold uppercase text-sm">
                        {previewResult.passed ? 'TRADE IDEA' : 'RESEARCH PLAN'}
                      </span>
                    </div>
                    <div className="text-xs text-gray-600">
                      Gate Score: {previewResult.gate_score}%
                    </div>
                  </div>

                  {/* Individual gates */}
                  <div className="space-y-1">
                    {previewResult.results.map((result) => (
                      <PreviewGateResult key={result.name} {...result} />
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Info box */}
          <div className="p-4 bg-gray-100 border-2 border-gray-300 text-xs">
            <div className="font-bold uppercase tracking-wider mb-2">How it works</div>
            <p className="text-gray-600">
              Events that pass all quality gates generate actionable Trade Ideas with
              entry/target/stop levels. Events that fail any gate generate Research Plans
              with questions to verify.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
