import { IBase } from "./ibase";

export interface IRegisterRequest extends IBase {
    email: string;
    password: string;
    confirmPassword: string;
}

export interface IRegisterResponse extends IBase {
    email: string
}