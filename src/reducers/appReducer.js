import * as types from '../actions/actionTypes';
import initialState from './initialState';

export default function appReducer(state = initialState.user, action) {
    switch (action.type) {
        case types.LOAD_USER_SUCCESS:
            return action.response.user;
        default:
            return state;
    }
}