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

export function loadCostCentres (committeeId) {
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

export function constructPart (data, committees, costCentres) {
    const { committee, cost_centre, budget_line } = data;
    const committeeObj = committees.filter(c => c.committee_id === committee)[0];
    const costCentreObj = costCentres.filter(cc => cc.cost_centre_id === cost_centre)[0];
    const budgetLineObj = costCentreObj.budget_lines.filter(bl => bl.budget_line_id === budget_line)[0];

    return {
        type: types.ADD_EXPENSE_PART,
        part: {
            amount: data.amount,
            budget_line_id: budget_line,
            budget_line_name: budgetLineObj.budget_line_name,
            committee_name: committeeObj.committee_name,
            cost_centre_name: costCentreObj.cost_centre_name
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
    const parts = newExpense.parts.map(p => ({
        budget_line_id: p.budget_line_id,
        amount: p.amount
    }));
    const payload = {
        description: newExpense.data.description,
        expense_date: newExpense.data.date,
        expense_parts: parts
    };

    return {
        type: CALL_API,
        [CALL_API]: {
            method: 'post',
            path: '/expense/',
            send: payload,
            sendingType: types.NEW_EXPENSE_SUBMIT,
            successType: types.NEW_EXPENSE_SUBMIT_SUCCESS,
            failureType: types.NEW_EXPENSE_SUBMIT_FAIL
        }
    }
}

export function setTitle (title) {
    return { type: types.SET_APP_TITLE, title: title }
}

export function startUpload () {
    return { type: types.EXPENSE_UPLOAD }
}

export function failUpload (err) {
    return { type: types.EXPENSE_UPLOAD_FAIL, response: err }
}

export function successUpload (res) {
    return { type: types.EXPENSE_UPLOAD_SUCCESS, response: res.body }
}

export function resetForm (res) {
    return { type: types.RESET_NEW_EXPENSE }
}