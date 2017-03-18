import * as types from './actionTypes';
import { CALL_API } from '../middleware/api';

export function loadProfile () {
    return {
        type: CALL_API,
        [CALL_API]: {
            method: 'get',
            path: '/user/current/',
            sendingType: types.LOAD_PROFILE,
            successType: types.LOAD_PROFILE_SUCCESS,
            failureType: types.LOAD_PROFILE_FAIL
        }
    }
}

export function textFieldChange (element, newValue) {
    return {
        type: types.PROFILE_MODEL_CHANGE,
        element: element,
        newValue: newValue
    }
}