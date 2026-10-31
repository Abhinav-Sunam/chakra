import { describe, it, expect } from 'vitest';
import { satPositionsAt } from './interpolate';
import { wrapLon } from '../lib/geo';
import { SatState } from '../net/types';

describe('interpolate & longitude wrap', () => {
  it('correctly wraps longitude at antimeridian [-180, 180]', () => {
    expect(wrapLon(185)).toBe(-175);
    expect(wrapLon(-185)).toBe(175);
    expect(Math.abs(wrapLon(180))).toBe(180);
    expect(wrapLon(-180)).toBe(-180);
    expect(Math.abs(wrapLon(540))).toBe(180);
  });

  it('interpolates satellite position with wrap', () => {
    const sats: SatState[] = [
      {
        id: 1,
        lat: 0,
        lon: 179.9,
        alt: 550,
        vlat: 0,
        vlon: 2.0, // moving east at 2 deg/s
        st: 0,
      },
    ];

    // 100ms later -> delta = +0.2 deg -> lon = 180.1 -> wrapped = -179.9
    const res = satPositionsAt(sats, 1000, 1100);
    expect(res[0].lon).toBeCloseTo(-179.9, 4);
    expect(res[0].lat).toBe(0);
  });
});
