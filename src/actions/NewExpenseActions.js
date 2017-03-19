import * as types from "./actionTypes";
import {CALL_API} from "../middleware/api";

export function textFieldChange (element, newValue) {
    return {
        type: types.NEW_EXPENSE_MODEL_CHANGE,
        element: element,
        newValue: newValue
    }
}

export function submitNewExpense (newExpense) {
    return {
        type: CALL_API,
        [CALL_API]: {
            method: 'put',
            path: '/expense/',
            send: newExpense,
            sendingType: types.NEW_EXPENSE_SUBMIT,
            successType: types.NEW_EXPENSE_SUBMIT_SUCCESS,
            failureType: types.NEW_EXPENSE_SUBMIT_FAIL
        }
    }
}