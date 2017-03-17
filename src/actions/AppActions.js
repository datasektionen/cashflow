import * as types from './actionTypes';
import { CALL_API } from '../middleware/api';

export function loadUser () {
    return {
        type: CALL_API,
        [CALL_API]: {
            method: 'get',
            path: '/user/current/',
            sendingType: types.LOAD_USER,
            successType: types.LOAD_USER_SUCCESS,
            failureType: types.LOAD_USER_FAIL
        }
    }
}
