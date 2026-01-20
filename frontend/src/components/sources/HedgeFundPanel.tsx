/**
 * Panel showing hedge fund 13F filing data.
 */
import { Building2, FileText, AlertCircle } from 'lucide-react';
import { useHedgeFunds } from '../../hooks/useSources';
import { formatDate } from '../../lib/utils';

export function HedgeFundPanel() {
  const { data, isLoading, error } = useHedgeFunds();

  if (isLoading) {
    return <LoadingState />;
  }

  if (error || data?.error) {
    return <ErrorState message={data?.error || 'Failed to load hedge fund data'} />;
  }

  const filings = data?.filings || [];
  const trackedFunds = data?.notable_funds?.length || 0;

  return (
    <div className="space-y-6">
      {/* Summary */}
      <div className="bg-white border border-gray-200 rounded-xl p-4">
        <div className="flex items-center gap-2 mb-4">
          <Building2 className="text-purple-600" size={20} />
          <h3 className="font-semibold">13F Filings Summary</h3>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-purple-50 rounded-lg p-4 text-center">
            <div className="text-2xl font-bold text-purple-700">
              {data?.filings_found || 0}
            </div>
            <div className="text-sm text-purple-600">Filings Found</div>
          </div>
          <div className="bg-purple-50 rounded-lg p-4 text-center">
            <div className="text-2xl font-bold text-purple-700">
              {trackedFunds}
            </div>
            <div className="text-sm text-purple-600">Tracked Funds</div>
          </div>
        </div>
      </div>

      {/* Recent filings */}
      <div>
        <h3 className="font-semibold mb-3">Recent Filings</h3>
        {filings.length === 0 ? (
          <p className="text-gray-500 text-sm">No recent filings found</p>
        ) : (
          <div className="space-y-3">
            {filings.slice(0, 10).map((filing: typeof filings[number], i: number) => (
              <div
                key={i}
                className="bg-white border border-gray-200 rounded-xl p-4 flex items-start gap-3"
              >
                <div className="p-2 bg-purple-100 rounded-lg">
                  <FileText className="text-purple-600" size={18} />
                </div>
                <div className="flex-1">
                  <div className="font-medium">{filing.fund_name}</div>
                  <div className="text-sm text-gray-500">CIK: {filing.cik}</div>
                  {filing.filing_date && (
                    <div className="text-xs text-gray-400 mt-1">
                      Filed: {formatDate(filing.filing_date)}
                    </div>
                  )}
                </div>
                {filing.accession_number && (
                  <a
                    href={`https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=${filing.cik}&type=13F`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:text-blue-700 text-sm"
                  >
                    View on SEC →
                  </a>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function LoadingState() {
  return (
    <div className="animate-pulse space-y-4">
      <div className="h-32 bg-gray-200 rounded-xl" />
      <div className="h-48 bg-gray-200 rounded-xl" />
    </div>
  );
}

function ErrorState({ message }: { message: string }) {
  return (
    <div className="bg-red-50 border border-red-200 rounded-xl p-6 flex items-center gap-3">
      <AlertCircle className="text-red-500" />
      <div>
        <p className="font-medium text-red-800">Error loading data</p>
        <p className="text-sm text-red-600">{message}</p>
      </div>
    </div>
  );
}
