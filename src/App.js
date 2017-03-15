import React, { Component } from 'react';
import AppBar from 'material-ui/AppBar';
import Drawer from 'material-ui/Drawer';
import MenuItem from 'material-ui/MenuItem';
import Subheader from 'material-ui/Subheader';
import Dashboard from 'material-ui/svg-icons/action/dashboard';

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
                    <Subheader>Cashfl0w</Subheader>
                    <MenuItem leftIcon={<Dashboard />} primaryText="Dashboard" />
                    <dashboard />
                    <Subheader>Inköp</Subheader>
                    <MenuItem primaryText="Alla inköp" />
                    <MenuItem primaryText="Bekräftade inköp" />
                    <MenuItem primaryText="Lägg till inköp" />
                </Drawer>

                <div style={contentStyle} className="content">
                    <AppBar title={"Cashfl0w"} onLeftIconButtonTouchTap={this.toggleDrawer} />
                </div>
            </div>
        );
    }
}

export default App;
