export interface ITransaction {
  date: string;
  description: string;
  icon: string;
  status: string;
  value: string;
  positive?: boolean;
}
