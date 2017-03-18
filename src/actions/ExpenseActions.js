import * as types from './actionTypes';
import { CALL_API } from '../middleware/api';

export function loadExpense (id) {
    return {
        type: CALL_API,
        [CALL_API]: {
            method: 'get',
            path: '/expense/' + id + '/',
            sendingType: types.LOAD_EXPENSE,
            successType: types.LOAD_EXPENSE_SUCCESS,
            failureType: types.LOAD_EXPENSE_FAIL
        }
    }
}

export function loadExpenseComments (id) {
    return {
        type: CALL_API,
        [CALL_API]: {
            method: 'get',
            path: '/expense/' + id + '/comments/',
            sendingType: types.LOAD_EXPENSE_COMMENTS,
            successType: types.LOAD_EXPENSE_COMMENTS_SUCCESS,
            failureType: types.LOAD_EXPENSE_COMMENTS_FAIL
        }
    }
}