import React, { Component } from 'react';

class Expenses extends Component {
    constructor (props) {
        super(props);
    }

    render () {
        return (
            <div>
                <h1>Expenses</h1>
                {this.props.children}
            </div>
        );
    }
}

export default Expenses;