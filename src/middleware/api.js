// middleware/api.js
// From https://www.codementor.io/reactjs/tutorial/intro-to-react-redux-pros

import superAgent from 'superagent';

export const CALL_API = Symbol('CALL_API');

export default store => next => action => {
    if (!action[CALL_API]) {
        return next(action);
    }
    let request = action[CALL_API];
    let { method, path, send, failureType, successType, sendingType } = request;
    let { dispatch } = store;
    path = "http://127.0.0.1:8000/api" + path;

    dispatch({ type: sendingType });
    superAgent[method](path)
        .withCredentials()
        .send(send)
        .end((err, res) => {
            if (err) {
                dispatch({
                    type: failureType,
                    response: err
                });
            } else {
                dispatch({
                    type: successType,
                    response: res.body
                });
            }
        });
};