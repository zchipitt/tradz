/**
 * Panel showing news articles.
 * Brutalist design aesthetic - black/white + yellow accent.
 */
import { ExternalLink, AlertCircle, Clock, Loader2 } from 'lucide-react';
import { useNews } from '../../hooks/useSources';
import { formatDate } from '../../lib/utils';
import type { NewsArticle } from '../../api/types';

export function NewsPanel() {
  const { data, isLoading, isFetching, error } = useNews();

  // Only show full loading state on initial load (no cached data)
  if (isLoading && !data) {
    return <LoadingState />;
  }

  if (error || data?.error) {
    return <ErrorState message={data?.error || 'Failed to load news data'} />;
  }

  const headlines = data?.headlines || [];
  const byTicker = data?.by_ticker || {};
  const tickers = Object.keys(byTicker);
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
            {data?.total_articles || 0}
          </div>
          <div className="text-[10px] uppercase tracking-wide font-bold text-gray-600">Total Articles</div>
        </div>
        <div className="bg-primary/20 border-2 border-black p-4 text-center">
          <div className="text-3xl font-bold">{tickers.length}</div>
          <div className="text-xs uppercase tracking-wide font-bold text-gray-600">Tickers Covered</div>
        </div>
      </div>

      {/* Headlines */}
      {headlines.length > 0 && (
        <div>
          <h3 className="text-xs font-bold uppercase tracking-wider mb-3 border-b-2 border-black pb-2">
            Market Headlines
          </h3>
          <div className="space-y-2">
            {headlines.slice(0, 5).map((article, i) => (
              <ArticleCard key={i} article={article} />
            ))}
          </div>
        </div>
      )}

      {/* News by ticker */}
      {tickers.length > 0 && (
        <div>
          <h3 className="text-xs font-bold uppercase tracking-wider mb-3 border-b-2 border-black pb-2">
            News by Ticker
          </h3>
          <div className="space-y-4">
            {tickers.slice(0, 5).map((ticker) => (
              <div key={ticker}>
                <h4 className="text-xs mb-2 flex items-center gap-2">
                  <span className="px-2 py-0.5 bg-gray-100 border-2 border-black font-bold">
                    ${ticker}
                  </span>
                  <span className="px-1.5 py-0.5 bg-primary border border-black font-bold text-black ml-1">
                    {byTicker[ticker].length} articles
                  </span>
                </h4>
                <div className="space-y-1 pl-3 border-l-2 border-gray-300">
                  {byTicker[ticker].slice(0, 3).map((article, i) => (
                    <ArticleRow key={i} article={article} />
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Footer */}
      <div className="text-xs text-gray-500 border-t-2 border-gray-200 pt-3">
        Displaying {headlines.length} headlines across {tickers.length} tickers
      </div>
    </div>
  );
}

function ArticleCard({ article }: { article: NewsArticle }) {
  return (
    <div className="bg-white border-2 border-black p-3 hover:bg-gray-50 transition-colors cursor-pointer">
      <div className="flex items-start gap-3">
        <div className="flex-1 min-w-0">
          <h4 className="font-bold text-sm leading-snug line-clamp-2">{article.title}</h4>
          <div className="flex items-center gap-3 mt-2 text-[10px]">
            {article.source && (
              <span className="px-1.5 py-0.5 bg-gray-100 border border-black uppercase font-bold">
                {article.source}
              </span>
            )}
            {article.published_at && (
              <span className="flex items-center gap-1 text-gray-500">
                <Clock size={10} />
                {formatDate(article.published_at)}
              </span>
            )}
          </div>
        </div>
        {article.url && (
          <a
            href={article.url}
            target="_blank"
            rel="noopener noreferrer"
            className="shrink-0 p-2 border border-black hover:bg-primary transition-colors"
          >
            <ExternalLink size={14} />
          </a>
        )}
      </div>
    </div>
  );
}

function ArticleRow({ article }: { article: NewsArticle }) {
  return (
    <div className="flex items-start justify-between gap-2 py-2">
      <div className="flex-1 min-w-0">
        <p className="text-xs text-gray-700 line-clamp-2">{article.title}</p>
        <div className="flex items-center gap-2 mt-1 text-[10px] text-gray-500">
          {article.source && <span>{article.source}</span>}
          {article.published_at && <span>· {formatDate(article.published_at)}</span>}
        </div>
      </div>
      {article.url && (
        <a
          href={article.url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-gray-500 hover:text-black shrink-0"
        >
          <ExternalLink size={12} />
        </a>
      )}
    </div>
  );
}

function LoadingState() {
  return (
    <div className="flex items-center justify-center py-12">
      <div className="flex items-center gap-3 border-2 border-black px-6 py-4 bg-gray-50">
        <Loader2 className="animate-spin" size={16} />
        <span className="text-sm font-bold uppercase">Loading News Feed...</span>
      </div>
    </div>
  );
}

function ErrorState({ message }: { message: string }) {
  return (
    <div className="bg-status-error/10 border-2 border-status-error p-4 flex items-center gap-3 font-mono">
      <AlertCircle className="text-status-error" size={16} />
      <div>
        <p className="font-bold text-status-error text-sm uppercase">Error: News Data Load Failed</p>
        <p className="text-xs text-gray-600">{message}</p>
      </div>
    </div>
  );
}
