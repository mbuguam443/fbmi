export interface User {
  id: number;
  username: string;
  first_name: string;
  last_name: string;
  full_name: string;
  email: string;
  phone: string;
  role: string;
  role_label: string;
  photo_url: string | null;
}

export interface Member {
  id: number;
  member_number: string;
  first_name: string;
  middle_name: string;
  last_name: string;
  full_name: string;
  gender: string;
  date_of_birth: string | null;
  phone: string;
  email: string;
  address: string;
  photo_url: string | null;
  date_joined: string | null;
  membership_status: string;
  membership_status_label: string;
  membership_type: string;
  membership_type_label: string;
  baptism_status: string;
  baptism_date: string | null;
  salvation_date: string | null;
  marital_status: string;
  occupation: string;
  emergency_contact_name: string;
  emergency_contact_phone: string;
  family: string | null;
}

export interface GivingRecord {
  id: number;
  amount: string;
  category: string;
  category_label: string;
  date: string;
  payment_method: string;
  payment_method_label: string;
  reference_number: string | null;
}

export interface AttendanceRecord {
  id: number;
  service: string;
  date: string;
  start_time: string | null;
  location: string;
  type: string;
  recorded: string;
}

export interface Group {
  id: number;
  name: string;
  description: string;
  meeting_day: string;
  meeting_time: string | null;
  location: string;
  leader: string | null;
  members_count: number;
  is_active: boolean;
}

export interface ChurchEvent {
  id: number;
  name: string;
  description: string;
  date: string;
  time: string | null;
  end_date: string | null;
  location: string;
  speaker: string | null;
  capacity: number | null;
  is_full: boolean;
  registrations_count: number;
  registration_required: boolean;
  registered: boolean;
}

export interface Announcement {
  id: number;
  title: string;
  message: string;
  publish_date: string;
  expiry_date: string | null;
  target_audience: string;
}

export interface Sermon {
  id: number;
  title: string;
  speaker: string | null;
  date: string;
  bible_verse: string | null;
  series: string | null;
  category: string | null;
  description: string | null;
  youtube_url: string | null;
}

export interface Prayer {
  id: number;
  title: string;
  request: string;
  category: string;
  category_label: string;
  date: string;
  status: string;
  status_label: string;
  is_confidential: boolean;
  is_mine: boolean;
}

export interface PortalCounts {
  groups: number;
  givings: number;
  givings_total: string;
  attendance: number;
  events: number;
  announcements: number;
}

export interface PortalData {
  member: Member | null;
  counts: PortalCounts;
  groups: Group[];
  givings: GivingRecord[];
  attendance: AttendanceRecord[];
  events: ChurchEvent[];
  announcements: Announcement[];
}

export interface LoginResponse {
  token: string;
  user: User;
  member: Member | null;
}

export interface ListResponse<T> {
  results: T[];
  count: number;
  total?: string;
}