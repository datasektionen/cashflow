import React, { Component } from 'react';
import Drawer from 'material-ui/Drawer';
import AppBar from 'material-ui/AppBar';
import { Link } from 'react-router';

import Nav from './containers/Nav';

import Person from 'material-ui/svg-icons/social/person';
import FlatButton from 'material-ui/FlatButton';

class App extends Component {
    constructor(props) {
        super(props);
        this.state = { drawerOpen: true };
        this.toggleDrawer = this.toggleDrawer.bind(this);
    }

    toggleDrawer() {
        this.setState({
            drawerOpen: !this.state.drawerOpen
        });
    }

    render() {
        const contentStyle = { transition: 'margin-left 450ms cubic-bezier(0.23, 1, 0.32, 1)' };

        if (this.state.drawerOpen)
            contentStyle.marginLeft = 256;

        const right = <FlatButton icon={<Person />} label="Britt-Marie" containerElement={<Link to="/profile" />} />;

        return (
            <div className="App">
                <Drawer open={this.state.drawerOpen}>
                    <Nav />
                </Drawer>

                <div style={contentStyle} className="content">
                    <AppBar title={"Cashfl0w"} onLeftIconButtonTouchTap={this.toggleDrawer} iconElementRight={right} />
                    <div style={{margin: 20}}>
                        {this.props.children}
                    </div>
                </div>
            </div>
        );
    }
}

export default App;
