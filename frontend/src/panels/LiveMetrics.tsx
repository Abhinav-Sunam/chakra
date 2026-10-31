import React, { useState, useEffect, useRef } from 'react';
import { useSimStore } from '../store/useSim';
import { AreaChart, Area, ResponsiveContainer } from 'recharts';
import { formatNumber, formatThroughput } from '../lib/format';
import { Activity, Radio, ArrowDown, ArrowUp } from 'lucide-react';

interface MetricHistoryPoint {
  t: number;
  latAdaptive: number;
  latStatic: number;
  pdrAdaptive: number;
  pdrStatic: number;
  thrAdaptive: number;
  thrStatic: number;
}

export const LiveMetrics: React.FC = () => {
  const { latestFrame, init, ui, setSelectedFlowId } = useSimStore();
  const [history, setHistory] = useState<MetricHistoryPoint[]>([]);
  const lastTimeRef = useRef<number>(0);

  useEffect(() => {
    if (!latestFrame) return;
    if (latestFrame.t === lastTimeRef.current) return;
    lastTimeRef.current = latestFrame.t;

    // Handle PDR whether backend sends [0, 1] fraction or [0, 100] percentage
    const normPdr = (val: number) => (val > 1.0 ? Math.min(val, 100) : Math.min(val * 100, 100));

    setHistory((prev) => {
      const point: MetricHistoryPoint = {
        t: latestFrame.t,
        latAdaptive: latestFrame.metrics.adaptive.latMs,
        latStatic: latestFrame.metrics.static.latMs,
        pdrAdaptive: normPdr(latestFrame.metrics.adaptive.pdr),
        pdrStatic: normPdr(latestFrame.metrics.static.pdr),
        thrAdaptive: latestFrame.metrics.adaptive.thrMbps / 1000,
        thrStatic: latestFrame.metrics.static.thrMbps / 1000,
      };
      const next = [...prev, point];
      if (next.length > 120) next.shift();
      return next;
    });
  }, [latestFrame]);

  if (!latestFrame) {
    return (
      <aside className="w-80 bg-panel border-l border-border p-4 flex flex-col justify-center items-center text-muted text-xs">
        <Activity className="w-6 h-6 animate-pulse mb-2 text-teal-bright" />
        Connecting to simulation stream...
      </aside>
    );
  }

  const { adaptive, static: stat, linkUptime, activeFailures } = latestFrame.metrics;
  const view = ui.view;

  // Latency delta (% improvement of adaptive over static)
  const latDelta = stat.latMs > 0 ? ((stat.latMs - adaptive.latMs) / stat.latMs) * 100 : 0;
  // Helper to normalize PDR to 0-100% display safely
  const formatPdrDisplay = (val: number) => {
    const pct = val > 1.0 ? Math.min(val, 100) : Math.min(val * 100, 100);
    return pct.toFixed(1);
  };

  const pdrValAdaptive = adaptive.pdr > 1.0 ? adaptive.pdr : adaptive.pdr * 100;
  const pdrValStatic = stat.pdr > 1.0 ? stat.pdr : stat.pdr * 100;
  const pdrDelta = pdrValAdaptive - pdrValStatic;

  return (
    <aside className="w-84 bg-panel border-l border-border flex flex-col select-none overflow-y-auto shrink-0 z-10">
      {/* Panel Header */}
      <div className="p-4 border-b border-border bg-panel2/40">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Activity className="w-4 h-4 text-teal-bright" />
            <h2 className="text-xs font-bold uppercase tracking-wider text-text">
              Live Network Metrics
            </h2>
          </div>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-panel2 text-muted border border-border">
            10 Hz Feed
          </span>
        </div>
      </div>

      <div className="p-4 space-y-4 flex-1">
        {/* Metric 1: End-to-End Latency */}
        <div className="bg-panel2/60 rounded-xl p-3 border border-border">
          <div className="flex items-center justify-between text-xs mb-1">
            <span className="text-muted font-medium">End-to-End Latency</span>
            {view === 'compare' && latDelta > 0 && (
              <span className="text-[10px] font-semibold text-teal-bright flex items-center">
                <ArrowDown className="w-3 h-3 mr-0.5" />
                {latDelta.toFixed(0)}% faster
              </span>
            )}
          </div>

          <div className="flex items-baseline justify-between mb-2">
            {view !== 'static' && (
              <div>
                <span className="text-xl font-bold text-teal-bright tabular-nums font-mono">
                  {formatNumber(adaptive.latMs)}
                </span>
                <span className="text-xs text-muted ml-1">ms (Adap)</span>
              </div>
            )}
            {view !== 'adaptive' && (
              <div>
                <span className="text-xl font-bold text-orange tabular-nums font-mono">
                  {formatNumber(stat.latMs)}
                </span>
                <span className="text-xs text-muted ml-1">ms (Stat)</span>
              </div>
            )}
          </div>

          {/* Sparkline */}
          <div className="h-10 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={history}>
                {view !== 'static' && (
                  <Area
                    type="monotone"
                    dataKey="latAdaptive"
                    stroke="#4FC3D9"
                    fill="rgba(79,195,217,0.15)"
                    strokeWidth={1.5}
                    isAnimationActive={false}
                  />
                )}
                {view !== 'adaptive' && (
                  <Area
                    type="monotone"
                    dataKey="latStatic"
                    stroke="#E8843A"
                    fill="rgba(232,132,58,0.15)"
                    strokeWidth={1.5}
                    isAnimationActive={false}
                  />
                )}
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Metric 2: Packet Delivery Ratio */}
        <div className="bg-panel2/60 rounded-xl p-3 border border-border">
          <div className="flex items-center justify-between text-xs mb-1">
            <span className="text-muted font-medium">Packet Delivery Ratio (PDR)</span>
            {view === 'compare' && pdrDelta > 0 && (
              <span className="text-[10px] font-semibold text-ok flex items-center">
                <ArrowUp className="w-3 h-3 mr-0.5" />
                +{pdrDelta.toFixed(1)}% PDR
              </span>
            )}
          </div>

          <div className="flex items-baseline justify-between mb-2">
            {view !== 'static' && (
              <div>
                <span
                  className={`text-xl font-bold tabular-nums font-mono ${
                    pdrValAdaptive >= 95 ? 'text-ok' : pdrValAdaptive >= 80 ? 'text-warn' : 'text-crit'
                  }`}
                >
                  {formatPdrDisplay(adaptive.pdr)}%
                </span>
                <span className="text-xs text-muted ml-1">(Adap)</span>
              </div>
            )}
            {view !== 'adaptive' && (
              <div>
                <span
                  className={`text-xl font-bold tabular-nums font-mono ${
                    pdrValStatic >= 95 ? 'text-ok' : pdrValStatic >= 80 ? 'text-warn' : 'text-crit'
                  }`}
                >
                  {formatPdrDisplay(stat.pdr)}%
                </span>
                <span className="text-xs text-muted ml-1">(Stat)</span>
              </div>
            )}
          </div>

          <div className="h-10 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={history}>
                {view !== 'static' && (
                  <Area
                    type="monotone"
                    dataKey="pdrAdaptive"
                    stroke="#3DD68C"
                    fill="rgba(61,214,140,0.15)"
                    strokeWidth={1.5}
                    isAnimationActive={false}
                  />
                )}
                {view !== 'adaptive' && (
                  <Area
                    type="monotone"
                    dataKey="pdrStatic"
                    stroke="#E8843A"
                    fill="rgba(232,132,58,0.15)"
                    strokeWidth={1.5}
                    isAnimationActive={false}
                  />
                )}
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Metric 3: Throughput & Reroutes */}
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div className="bg-panel2/60 rounded-xl p-3 border border-border">
            <div className="text-muted text-[10px] uppercase font-semibold mb-1">Throughput</div>
            <div className="text-sm font-bold text-text tabular-nums font-mono">
              {view === 'static' ? formatThroughput(stat.thrMbps) : formatThroughput(adaptive.thrMbps)}
            </div>
            <div className="text-[10px] text-muted mt-1">Aggregated delivered</div>
          </div>

          <div className="bg-panel2/60 rounded-xl p-3 border border-border">
            <div className="text-muted text-[10px] uppercase font-semibold mb-1">Reroutes Done</div>
            <div className="text-sm font-bold text-teal-bright tabular-nums font-mono">
              {adaptive.reroutes} <span className="text-[10px] text-muted">({adaptive.rerouteRate}/min)</span>
            </div>
            <div className="text-[10px] text-muted mt-1">
              Proactive: {latestFrame.metrics.proactiveReroutes ?? 0} | Reactive: {latestFrame.metrics.reactiveReroutes ?? 0}
            </div>
          </div>
        </div>

        {/* Partition & Storm Warning Banner */}
        {latestFrame.graph_partitioned && (
          <div className="p-2.5 rounded-lg bg-crit/15 border border-crit/40 text-crit text-xs font-semibold flex items-center space-x-2">
            <span className="w-2 h-2 rounded-full bg-crit animate-ping" />
            <span>Network Partitioned ({latestFrame.isolated_stations?.length ?? 0} stations isolated)</span>
          </div>
        )}

        {latestFrame.storms && latestFrame.storms.length > 0 && (
          <div className="p-2 rounded-lg bg-orange/15 border border-orange/40 text-orange text-[11px] font-medium flex items-center justify-between">
            <span>⛈️ Active Atmospheric Storm Cells</span>
            <span className="font-mono font-bold">{latestFrame.storms.length} cell(s)</span>
          </div>
        )}

        {/* Metric 4: Link Uptime & Failures */}
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div className="bg-panel2/60 rounded-xl p-3 border border-border">
            <div className="text-muted text-[10px] uppercase font-semibold mb-1">Link Uptime</div>
            <div className="text-sm font-bold text-text tabular-nums font-mono">
              {(linkUptime > 1.0 ? linkUptime : linkUptime * 100).toFixed(1)}%
            </div>
            <div className="text-[10px] text-muted mt-1">Physical network</div>
          </div>

          <div className="bg-panel2/60 rounded-xl p-3 border border-border">
            <div className="text-muted text-[10px] uppercase font-semibold mb-1">Active Outages</div>
            <div
              className={`text-sm font-bold tabular-nums font-mono ${
                activeFailures > 0 ? 'text-crit' : 'text-ok'
              }`}
            >
              {activeFailures} {activeFailures === 1 ? 'failure' : 'failures'}
            </div>
            <div className="text-[10px] text-muted mt-1">Recovery ~{adaptive.recoverS}s</div>
          </div>
        </div>

        {/* Flows List */}
        <div className="mt-4 pt-4 border-t border-border">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-text uppercase tracking-wide">
              Active Flows (8)
            </span>
            <span className="text-[10px] text-muted">Click to inspect path</span>
          </div>

          <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
            {latestFrame.flows.map((flow) => {
              const isSelected = ui.selectedFlowId === flow.id;
              const isAdaptiveBlackholed = flow.adaptive.blackholed;
              const isStaticBlackholed = flow.static.blackholed;

              return (
                <button
                  key={flow.id}
                  onClick={() => setSelectedFlowId(isSelected ? null : flow.id)}
                  className={`w-full flex items-center justify-between p-2 rounded-lg text-left text-xs transition border ${
                    isSelected
                      ? 'bg-panel2 border-teal-bright text-text font-semibold shadow-sm'
                      : 'bg-panel2/30 border-border/50 text-muted hover:text-text hover:bg-panel2/60'
                  }`}
                >
                  <div className="flex items-center space-x-2">
                    <span
                      className={`w-2 h-2 rounded-full ${
                        view === 'static'
                          ? isStaticBlackholed ? 'bg-crit' : 'bg-orange'
                          : isAdaptiveBlackholed ? 'bg-crit' : 'bg-teal-bright'
                      }`}
                    />
                    <span className="font-mono text-xs">{flow.id}</span>
                  </div>

                  <div className="font-mono text-[11px] text-right">
                    {view === 'static' ? (
                      <span className={isStaticBlackholed ? 'text-crit font-bold' : 'text-text'}>
                        {isStaticBlackholed ? 'OUTAGE' : `${flow.static.ms.toFixed(0)}ms`}
                      </span>
                    ) : (
                      <span className={isAdaptiveBlackholed ? 'text-crit font-bold' : 'text-teal-bright'}>
                        {isAdaptiveBlackholed ? 'OUTAGE' : `${flow.adaptive.ms.toFixed(0)}ms`}
                      </span>
                    )}
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      </div>
    </aside>
  );
};
