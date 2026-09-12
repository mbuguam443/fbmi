export const Colors = {
  bg: '#F8F9FA',
  card: '#FFFFFF',
  navy: '#6794A6',
  navyDark: '#4D7A8A',
  gold: '#BAA883',
  goldLight: '#D4C8A8',
  text: '#343A40',
  muted: '#6C757D',
  border: '#E9ECEF',
  danger: '#BF2D30',
  success: '#2E7D32',
  info: '#546280',
};

export const Radius = {
  sm: 8,
  md: 12,
  lg: 16,
};

export const Spacing = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 24,
};

export const Shadow = {
  shadowColor: '#000',
  shadowOffset: { width: 0, height: 1 },
  shadowOpacity: 0.06,
  shadowRadius: 3,
  elevation: 2,
};

export function formatDate(iso?: string | null): string {
  if (!iso) return '—';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '—';
  return d.toLocaleDateString('en-KE', { day: 'numeric', month: 'short', year: 'numeric' });
}

export function formatMoney(amount?: string | number | null): string {
  if (amount === null || amount === undefined || amount === '') return 'KES 0';
  const n = Number(amount);
  if (Number.isNaN(n)) return String(amount);
  const opts = n % 1 === 0 ? { maximumFractionDigits: 0 } : { minimumFractionDigits: 2, maximumFractionDigits: 2 };
  return `KES ${n.toLocaleString('en-KE', opts)}`;
}

export function initials(name?: string | null): string {
  if (!name) return 'FB';
  return name
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((p) => p.charAt(0).toUpperCase())
    .join('');
}