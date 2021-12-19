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

import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';

import { ISettingRegistry } from '@jupyterlab/settingregistry';

import { requestAPI } from './handler';

/**
 * Initialization data for the swm-jupyter-term extension.
 */
const plugin: JupyterFrontEndPlugin<void> = {
  id: 'swm-jupyter-term:plugin',
  autoStart: true,
  optional: [ISettingRegistry, ICommandPalette, IMainMenu],
  activate: (app: JupyterFrontEnd, settingRegistry: ISettingRegistry | null, palette: ICommandPalette,  mainMenu: IMainMenu) => {
    console.log('JupyterLab extension swm-jupyter-term is activated!');

    if (settingRegistry) {
      settingRegistry
        .load(plugin.id)
        .then(settings => {
          console.log('swm-jupyter-term settings loaded:', settings.composite);
        })
        .catch(reason => {
          console.error('Failed to load settings for swm-jupyter-term.', reason);
        });
    }

    const { commands } = app;
    const skyportMenu: Menu = new Menu({ commands });
    skyportMenu.title.label = 'Sky Port';
    mainMenu.addMenu(skyportMenu, { rank: 80 });

    add_config_jobs(skyportMenu, palette, app);
    add_config_resources(skyportMenu, palette, app);
    add_config_config(skyportMenu, palette, app);
  }
};

export default plugin;


function add_config_config(skyport_menu: Menu, palette: ICommandPalette, app: JupyterFrontEnd) {
    const category = 'Sky Port';
    const command = 'swm-jupyter-term:main-menu-config';
    app.commands.addCommand(command, {
      label: 'Configure Spawner',
      caption: 'Configure Sky Port',
      execute: (args: any) => {
        create_main_area_widget("swm-jupyter-term:config", "Sky Port Configuration", app);
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
    const command = 'swm-jupyter-term:main-menu-jobs';
    app.commands.addCommand(command, {
      label: 'Show Jobs',
      caption: 'Show Sky Port jobs of the current user',
      execute: (args: any) => {
        let widget = create_main_area_widget("swm-jupyter-term:jobs", "Sky Port Jobs", app);
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
    const command = 'swm-jupyter-term:main-menu-res';
    app.commands.addCommand(command, {
      label: 'Show Resources',
      caption: 'Show Sky Port resources',
      execute: (args: any) => {
        create_main_area_widget("swm-jupyter-term:res", "Sky Port Resources", app);
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

async function fetch_jobs(widget: MainAreaWidget) {
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

    requestAPI<any>('get_example')
      .then(data => {
        console.log(data);
      })
      .catch(reason => {
        console.error(
          `The swm_jupyter_term server extension appears to be missing.\n${reason}`
        );
      });

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
