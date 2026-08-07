import React from 'react';
import { VENDOR_LABEL, vendorColor } from '@/lib/format';

export function VendorBadge({ vendor }) {
  const color = vendorColor(vendor);
  return (
    <span
      className="inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-[11px] font-medium border"
      style={{ color, borderColor: color + '55', background: color + '14' }}
      data-testid={`vendor-badge-${vendor}`}
    >
      <span className="inline-block w-1.5 h-1.5 rounded-full" style={{ background: color }} />
      {VENDOR_LABEL[vendor] || vendor}
    </span>
  );
}
