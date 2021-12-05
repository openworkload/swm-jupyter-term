import {
    JupyterFrontEnd,
    JupyterFrontEndPlugin
} from '@jupyterlab/application';

import {
    ICommandPalette,
    MainAreaWidget
} from '@jupyterlab/apputils';

import {
    Menu,
    Widget
} from '@lumino/widgets';

import {
    IMainMenu
} from '@jupyterlab/mainmenu';

//import * as fs from 'fs-extra';
//import * as fs from "fs";
import {promises as fs} from 'fs';
//import fs from 'fs';

/**
 * Initialization data for the swm-jupyter-terminal extension.
 */
const extension: JupyterFrontEndPlugin<void> = {
  id: 'swm-jupyter-terminal:plugin',
  autoStart: true,
  requires: [ICommandPalette, IMainMenu],
  activate: (app: JupyterFrontEnd, palette: ICommandPalette,  mainMenu: IMainMenu) => {
    console.log('JupyterLab extension swm-jupyter-terminal is activated');

    const { commands } = app;
    const skyportMenu: Menu = new Menu({ commands });
    skyportMenu.title.label = 'Sky Port';
    mainMenu.addMenu(skyportMenu, { rank: 80 });

    add_config_jobs(skyportMenu, palette, app);
    add_config_resources(skyportMenu, palette, app);
    add_config_config(skyportMenu, palette, app);
  }
};

export default extension;

function add_config_config(skyport_menu: Menu, palette: ICommandPalette, app: JupyterFrontEnd) {
    const category = 'Sky Port';
    const command = 'swm-jupyter-terminal:main-menu-config';
    app.commands.addCommand(command, {
      label: 'Configure Spawner',
      caption: 'Configure Sky Port',
      execute: (args: any) => {
        create_main_area_widget("swm-jupyter-terminal:config", "Sky Port Configuration", app);
      }
    });
    palette.addItem({
      command,
      category,
      args: { origin: 'Configure Sky Port' }
    });
    skyport_menu.addItem({ command, args: { origin: 'Sky Port' } });
}

function add_config_jobs(skyport_menu: Menu, palette: ICommandPalette, app: JupyterFrontEnd) {
    const category = 'Sky Port';
    const command = 'swm-jupyter-terminal:main-menu-jobs';
    app.commands.addCommand(command, {
      label: 'Show Jobs',
      caption: 'Show Sky Port jobs of the current user',
      execute: (args: any) => {
        let widget = create_main_area_widget("swm-jupyter-terminal:jobs", "Sky Port Jobs", app);
        fetch_jobs(widget);
      }
    });
    palette.addItem({
      command,
      category,
      args: { origin: 'Show Sky Port jobs' }
    });
    skyport_menu.addItem({ command, args: { origin: 'Sky Port' } });
}

function add_config_resources(skyport_menu: Menu, palette: ICommandPalette, app: JupyterFrontEnd) {
    const category = 'Sky Port';
    const command = 'swm-jupyter-terminal:main-menu-res';
    app.commands.addCommand(command, {
      label: 'Show Resources',
      caption: 'Show Sky Port resources',
      execute: (args: any) => {
        create_main_area_widget("swm-jupyter-terminal:res", "Sky Port Resources", app);
      }
    });
    palette.addItem({
      command,
      category,
      args: { origin: 'Show Sky Port resources' }
    });
    skyport_menu.addItem({ command, args: { origin: 'Sky Port' } });
}

function create_main_area_widget(id: string, label: string, app: JupyterFrontEnd) {
    const content = new Widget();
    const widget = new MainAreaWidget({ content });

    widget.id = id;
    widget.title.label = label;
    widget.title.closable = true;

    if (!widget.isAttached) {
        app.shell.add(widget, 'main');
    }
    app.shell.activateById(widget.id);

    return widget;
}

function add_table_cell(item: Node, row: Element) {
  let cell = document.createElement("td");
  cell.appendChild(item);
  row.appendChild(cell);
}

function fetch_jobs(widget: MainAreaWidget) {
    console.log('Fetch Sky Port jobs');
    let table = document.createElement("table");
    table.setAttribute("border", "2");

    var table_body = document.createElement("tbody");

    var header_row = document.createElement("tr");
    add_table_cell(document.createTextNode("ID"), header_row);
    add_table_cell(document.createTextNode("Name"), header_row);
    add_table_cell(document.createTextNode("Submit"), header_row);
    add_table_cell(document.createTextNode("Start"), header_row);
    add_table_cell(document.createTextNode("End"), header_row);
    add_table_cell(document.createTextNode("Nodes"), header_row);
    add_table_cell(document.createTextNode("Resources"), header_row);
    table_body.appendChild(header_row);

    //const fs = require('fs-extra')
    var https = require('https');
    //var fs  = require('fs-extra');
    let options = {
      hostname: 'ts',
      port: 8443,
      path: '/user/job',
      method: 'GET',
      key: fs.readFile('/home/taras/.swm/key.pem'),
      cert: fs.readFile('/home/taras/.swm/key.cert')
    };
    console.log(options);
    let req = https.request(options, function(res: any) {
      console.log(res.statusCode);
      res.on('data', function(d: any) {
                       process.stdout.write(d);
                     }
            );
    });
    req.end();


    for (var i = 0; i < 2; i++) {
      var row = document.createElement("tr");
      for (var j = 0; j < 7; j++) {
        var cell = document.createElement("td");
        var cellText = document.createTextNode("column "+j);
        cell.appendChild(cellText);
        row.appendChild(cell);
      }
      table_body.appendChild(row);
    }
    table.appendChild(table_body);

    widget.node.appendChild(table);
}
