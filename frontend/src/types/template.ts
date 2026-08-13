export interface BrandingConfig {
  logoEnabled: boolean;
  signatureEnabled: boolean;
  footerEnabled: boolean;
  letterheadEnabled: boolean;
  companyDetailsEnabled: boolean;
}

export interface ChannelData {
  enabled: boolean;
  subject?: string;
  content: string;
}

export interface Channels {
  [key: string]: ChannelData;
}

export type SectionType = 'RichText' | 'Table' | 'PeoplePicker' | 'Date' | 'Checklist' | 'FileUpload';

export interface SectionData {
  id: string;
  name: string;
  type: SectionType;
  enabled: boolean;
  order: number;
  required: boolean;
  defaultContent: any;
}

export interface ChecklistItem {
  id: string;
  title: string;
  description: string;
  mandatory: boolean;
  ownerRole: string;
  evidenceRequired: boolean;
}

export interface AudienceSelection {
  allEmployees: boolean;
  departments: string[];
  locations: string[];
  roles: string[];
}

export interface NotificationBehavior {
  requireAcknowledgement: boolean;
  allowComments: boolean;
}

export interface PublishingConfig {
  priority: string;
  publishImmediately: boolean;
  effectiveDate: string;
  expiryDate: string;
  audience: AudienceSelection;
  notificationBehavior: NotificationBehavior;
}

export type EventType = 'Birthday' | 'Anniversary' | 'Promotion' | 'New Joiner' | 'Farewell' | 'Certification' | 'Award' | 'Wedding' | 'Baby' | 'Achievement';

export interface EventTrigger {
  enabled: boolean;
  eventType: EventType;
  autoGenerate: boolean;
  autoPublish: boolean;
  leadTimeDays: number;
}

export interface Template {
  id: string;
  name: string;
  description: string;
  purpose: string;
  department: string;
  category: string;
  status: string;
  owner: string;
  created_by: string;
  updated_by: string;
  version: number;
  language: string;
  visibility: string;
  tags: string[];
  branding: BrandingConfig;
  channels: Channels;
  allowed_attachments: string[];
  sections: SectionData[];
  checklistItems: ChecklistItem[];
  signoffRole: string;
  publishing: PublishingConfig;
  eventTrigger: EventTrigger;
  banner: string;
  variables: string[];
  approval_required: boolean;
  approved_by: string;
  created_at: string;
  updated_at: string;
}

export interface Variable {
  id: string;
  name: string;
  display_name: string;
  type: "String" | "Number" | "Date" | "Boolean" | "Image";
  category: string;
  required: boolean;
  default_value: string;
  description: string;
}
