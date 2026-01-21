/**
 * Panel showing hedge fund 13F filing data.
 * Brutalist design aesthetic - black/white + yellow accent.
 */
import { FileText, AlertCircle, Loader2, ExternalLink } from 'lucide-react';
import { useHedgeFunds } from '../../hooks/useSources';
import { formatDate } from '../../lib/utils';

export function HedgeFundPanel() {
  const { data, isLoading, isFetching, error } = useHedgeFunds();

  // Only show full loading state on initial load (no cached data)
  if (isLoading && !data) {
    return <LoadingState />;
  }

  if (error || data?.error) {
    return <ErrorState message={data?.error || 'Failed to load hedge fund data'} />;
  }

  const filings = data?.filings || [];
  const trackedFunds = data?.notable_funds?.length || 0;
  const isRefreshing = isFetching && !!data;

  return (
    <div className="space-y-4 relative">
      {/* Refreshing indicator */}
      {isRefreshing && (
        <div className="absolute top-0 right-0 flex items-center gap-2 text-xs text-gray-500">
          <Loader2 className="animate-spin" size={12} />
          <span>REFRESHING...</span>
        </div>
      )}

      {/* Summary */}
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-white border-2 border-black p-4 text-center">
          <div className="text-3xl font-bold">
            {data?.filings_found || 0}
          </div>
          <div className="text-[10px] uppercase tracking-wide font-bold text-gray-600">Filings Found</div>
        </div>
        <div className="bg-primary/20 border-2 border-black p-4 text-center">
          <div className="text-3xl font-bold">
            {trackedFunds}
          </div>
          <div className="text-xs uppercase tracking-wide font-bold text-gray-600">Tracked Funds</div>
        </div>
      </div>

      {/* Recent filings */}
      <div>
        <h3 className="text-xs font-bold uppercase tracking-wider mb-3 border-b-2 border-black pb-2">
          Recent 13F Filings
        </h3>
        {filings.length === 0 ? (
          <div className="text-gray-500 text-sm py-4 border-2 border-gray-200 p-4 text-center">
            No recent filings found
          </div>
        ) : (
          <div className="space-y-2">
            {filings.slice(0, 10).map((filing: typeof filings[number], i: number) => (
              <div
                key={i}
                className="bg-white border-2 border-black p-3 flex items-start gap-3 hover:bg-gray-50 transition-colors cursor-pointer"
              >
                <div className="p-2 bg-gray-100 border-2 border-black">
                  <FileText size={14} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="font-bold text-sm truncate">{filing.fund_name}</div>
                  <div className="text-xs text-gray-500">CIK: {filing.cik}</div>
                  {filing.filing_date && (
                    <div className="text-[10px] text-gray-600 mt-1">
                      Filed: {formatDate(filing.filing_date)}
                    </div>
                  )}
                </div>
                {filing.accession_number && (
                  <a
                    href={`https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=${filing.cik}&type=13F`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1 text-[10px] font-bold hover:underline shrink-0 px-2 py-1 border border-black hover:bg-primary transition-colors"
                  >
                    <ExternalLink size={10} />
                    SEC
                  </a>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="text-xs text-gray-500 border-t-2 border-gray-200 pt-3">
        Displaying {Math.min(filings.length, 10)} of {filings.length} filings
      </div>
    </div>
  );
}

function LoadingState() {
  return (
    <div className="flex items-center justify-center py-12">
      <div className="flex items-center gap-3 border-2 border-black px-6 py-4 bg-gray-50">
        <Loader2 className="animate-spin" size={16} />
        <span className="text-sm font-bold uppercase">Loading 13F Filings...</span>
      </div>
    </div>
  );
}

function ErrorState({ message }: { message: string }) {
  return (
    <div className="bg-status-error/10 border-2 border-status-error p-4 flex items-center gap-3 font-mono">
      <AlertCircle className="text-status-error" size={16} />
      <div>
        <p className="font-bold text-status-error text-sm uppercase">Error: 13F Data Load Failed</p>
        <p className="text-xs text-gray-600">{message}</p>
      </div>
    </div>
  );
}
