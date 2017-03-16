import * as types from './actionTypes';
import { CALL_API } from '../middleware/api';

export function loadExpenses () {
    return {
        type: CALL_API,
        [CALL_API]: {
            method: 'get',
            path: '/expense/',
            sendingType: types.LOAD_EXPENSES,
            successType: types.LOAD_EXPENSES_SUCCESS,
            failureType: types.LOAD_EXPENSES_FAIL
        }
    }
}