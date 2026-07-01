import { IBase } from "./ibase";

export interface ILoginRequest extends IBase {
    email: string;
    password: string;
}

export interface ILoginResponse extends IBase {
    accessToken: string;
    tokenType: string;
}