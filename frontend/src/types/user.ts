export type Role = "Admin" | "Editor" | "Employee";

export interface User {
  id: string;
  name: string;
  email: string;
  role: Role;
}
