import React, { Component } from 'react';
import AppBar from 'material-ui/AppBar';
import Drawer from 'material-ui/Drawer';
import MenuItem from 'material-ui/MenuItem';
import Subheader from 'material-ui/Subheader';
import DashboardIcon from 'material-ui/svg-icons/action/dashboard';
import { green700 } from 'material-ui/styles/colors';

import Dashboard from './Dashboard';

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

        return (
            <div className="App">
                <Drawer open={this.state.drawerOpen}>
                    <AppBar title="Cashfl0w" style={{background: green700}} iconStyleLeft={{display: "none"}} />
                    <Subheader>Cashfl0w</Subheader>
                    <MenuItem leftIcon={<DashboardIcon />} primaryText="Dashboard" />
                    <dashboard />
                    <Subheader>Inköp</Subheader>
                    <MenuItem primaryText="Mina inköp" />
                    <MenuItem primaryText="Lägg till inköp" />
                    <Subheader>Profil</Subheader>
                    <MenuItem primaryText="Redigera min profil" />
                </Drawer>

                <div style={contentStyle} className="content">
                    <AppBar title={"Cashfl0w"} onLeftIconButtonTouchTap={this.toggleDrawer} />
                    {this.props.children || <Dashboard />}
                </div>
            </div>
        );
    }
}

export default App;
