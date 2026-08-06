export interface MasterDataItem {
  id: string;
  name: string;
  active: boolean;
  parentId?: string | null;
}

export interface PriorityItem {
  id: string;
  name: string;
  active: boolean;
  order: number;
  badgeClass: string;
  description: string;
  requiresAcknowledgementDefault: boolean;
}

export interface SimpleList {
  items: MasterDataItem[];
}

export interface LanguageList {
  items: MasterDataItem[];
  default: string;
}

export interface PriorityList {
  items: PriorityItem[];
}

export interface MasterDataLists {
  categories: SimpleList;
  departments: SimpleList;
  languages: LanguageList;
  priorities: PriorityList;
}

export interface MasterData {
  updatedBy: string;
  updatedAt: string;
  lists: MasterDataLists;
}
