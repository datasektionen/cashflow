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

export function submitProfile (profile) {
    const data = Object.assign({}, profile);
    delete data.default_account;

    return {
        type: CALL_API,
        [CALL_API]: {
            method: 'patch',
            path: '/user/' + profile.username + '/',
            send: data,
            sendingType: types.PROFILE_SUBMIT,
            successType: types.PROFILE_SUBMIT_SUCCESS,
            failureType: types.PROFILE_SUBMIT_FAIL
        }
    }
}