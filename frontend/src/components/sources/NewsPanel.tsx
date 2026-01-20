/**
 * Panel showing news articles.
 */
import { Newspaper, ExternalLink, AlertCircle, Clock } from 'lucide-react';
import { useNews } from '../../hooks/useSources';
import { formatDate } from '../../lib/utils';
import type { NewsArticle } from '../../api/types';

export function NewsPanel() {
  const { data, isLoading, error } = useNews();

  if (isLoading) {
    return <LoadingState />;
  }

  if (error || data?.error) {
    return <ErrorState message={data?.error || 'Failed to load news data'} />;
  }

  const headlines = data?.headlines || [];
  const byTicker = data?.by_ticker || {};
  const tickers = Object.keys(byTicker);

  return (
    <div className="space-y-6">
      {/* Summary */}
      <div className="bg-white border border-gray-200 rounded-xl p-4">
        <div className="flex items-center gap-2 mb-4">
          <Newspaper className="text-orange-600" size={20} />
          <h3 className="font-semibold">News Overview</h3>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-orange-50 rounded-lg p-4 text-center">
            <div className="text-2xl font-bold text-orange-700">
              {data?.summary?.total_articles || 0}
            </div>
            <div className="text-sm text-orange-600">Total Articles</div>
          </div>
          <div className="bg-orange-50 rounded-lg p-4 text-center">
            <div className="text-2xl font-bold text-orange-700">{tickers.length}</div>
            <div className="text-sm text-orange-600">Tickers Covered</div>
          </div>
        </div>
      </div>

      {/* Headlines */}
      {headlines.length > 0 && (
        <div>
          <h3 className="font-semibold mb-3">Market Headlines</h3>
          <div className="space-y-3">
            {headlines.slice(0, 5).map((article, i) => (
              <ArticleCard key={i} article={article} />
            ))}
          </div>
        </div>
      )}

      {/* News by ticker */}
      {tickers.length > 0 && (
        <div>
          <h3 className="font-semibold mb-3">News by Ticker</h3>
          <div className="space-y-4">
            {tickers.slice(0, 5).map((ticker) => (
              <div key={ticker}>
                <h4 className="font-medium text-gray-700 mb-2 flex items-center gap-2">
                  <span className="px-2 py-0.5 bg-gray-100 rounded text-sm">{ticker}</span>
                  <span className="text-xs text-gray-400">
                    ({byTicker[ticker].length} articles)
                  </span>
                </h4>
                <div className="space-y-2 pl-4 border-l-2 border-gray-100">
                  {byTicker[ticker].slice(0, 3).map((article, i) => (
                    <ArticleRow key={i} article={article} />
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function ArticleCard({ article }: { article: NewsArticle }) {
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-4">
      <div className="flex items-start gap-3">
        <div className="flex-1">
          <h4 className="font-medium text-gray-900 leading-snug">{article.title}</h4>
          <div className="flex items-center gap-3 mt-2 text-xs text-gray-500">
            {article.source && <span>{article.source}</span>}
            {article.published_at && (
              <span className="flex items-center gap-1">
                <Clock size={12} />
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
            className="text-orange-600 hover:text-orange-700 shrink-0"
          >
            <ExternalLink size={16} />
          </a>
        )}
      </div>
    </div>
  );
}

function ArticleRow({ article }: { article: NewsArticle }) {
  return (
    <div className="flex items-start justify-between gap-2 py-2">
      <div className="flex-1">
        <p className="text-sm text-gray-700 line-clamp-2">{article.title}</p>
        <div className="flex items-center gap-2 mt-1 text-xs text-gray-400">
          {article.source && <span>{article.source}</span>}
          {article.published_at && <span>· {formatDate(article.published_at)}</span>}
        </div>
      </div>
      {article.url && (
        <a
          href={article.url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-gray-400 hover:text-orange-600 shrink-0"
        >
          <ExternalLink size={14} />
        </a>
      )}
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
