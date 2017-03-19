import * as types from "./actionTypes";
import {CALL_API} from "../middleware/api";

export function loadCommittees () {
    return {
        type: CALL_API,
        [CALL_API]: {
            method: 'get',
            path: '/committees/',
            sendingType: types.LOAD_COMMITTEES,
            successType: types.LOAD_COMMITTEES_SUCCESS,
            failureType: types.LOAD_COMMITTEES_FAIL
        }
    }
}

export function loadCostCentre (committeeId) {
    return {
        type: CALL_API,
        [CALL_API]: {
            method: 'get',
            path: '/cost_centre/' + committeeId + '/',
            sendingType: types.LOAD_COST_CENTRES,
            successType: types.LOAD_COST_CENTRES_SUCCESS,
            failureType: types.LOAD_COST_CENTRES_FAIL
        }
    }
}


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