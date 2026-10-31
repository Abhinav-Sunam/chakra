import { IconLayer, LineLayer, PathLayer, ScatterplotLayer, TextLayer, PolygonLayer, GeoJsonLayer } from '@deck.gl/layers/typed';
import { TripsLayer } from '@deck.gl/geo-layers/typed';
import { SatState, LinkState, GroundStation, FlowPair } from '../net/types';

// Palette definitions matching SPEC §14 & Design system
export const TEAL_BRIGHT: [number, number, number] = [79, 195, 217];
export const TEAL: [number, number, number] = [58, 147, 168];
export const ORANGE: [number, number, number] = [232, 132, 58];
export const OK: [number, number, number] = [61, 214, 140];
export const WARN: [number, number, number] = [245, 185, 66];
export const CRIT: [number, number, number] = [229, 72, 77];
export const WHITE: [number, number, number] = [255, 255, 255];
export const GOLD: [number, number, number] = [255, 215, 0];

export interface MapLayerConfig {
  showFootprints: boolean;
  showDayNight: boolean;
  showParticles: boolean;
  showTrails: boolean;
  showStorms: boolean;
}

export interface StormCell {
  id: string;
  lat: number;
  lon: number;
  radius_km: number;
  intensity: number;
}

/**
 * Build day/night terminator polygon covering the night side of Earth.
 */
export function buildNightTerminator(tSim: number = 0): [number, number][] {
  const hour = ((tSim / 3600.0) % 24 + 12) % 24;
  const subsolarLon = (180 - (hour / 24.0) * 360.0);
  const nightCenterLon = ((subsolarLon + 180 + 180) % 360) - 180;

  const coords: [number, number][] = [];
  coords.push([nightCenterLon - 90, 85]);
  coords.push([nightCenterLon, 85]);
  coords.push([nightCenterLon + 90, 85]);
  coords.push([nightCenterLon + 90, -85]);
  coords.push([nightCenterLon, -85]);
  coords.push([nightCenterLon - 90, -85]);
  coords.push([nightCenterLon - 90, 85]);

  return coords;
}
