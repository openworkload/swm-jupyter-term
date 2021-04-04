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
    skyportMenu.title.label = 'SkyPort';
    mainMenu.addMenu(skyportMenu, { rank: 80 });

    add_config_jobs(skyportMenu, palette, app);
    add_config_resources(skyportMenu, palette, app);
    add_config_config(skyportMenu, palette, app);
  }
};

export default extension;

function add_config_config(skyport_menu: Menu, palette: ICommandPalette, app: JupyterFrontEnd) {
    const category = 'SkyPort';
    const command = 'swm-jupyter-terminal:main-menu-config';
    app.commands.addCommand(command, {
      label: 'Configure Spawner',
      caption: 'Configure SkyPort',
      execute: (args: any) => {
        create_main_area_widget("swm-jupyter-terminal:config", "SkyPort Configuration", app);
      }
    });
    palette.addItem({
      command,
      category,
      args: { origin: 'Configure SkyPort' }
    });
    skyport_menu.addItem({ command, args: { origin: 'SkyPort' } });
}

function add_config_jobs(skyport_menu: Menu, palette: ICommandPalette, app: JupyterFrontEnd) {
    const category = 'SkyPort';
    const command = 'swm-jupyter-terminal:main-menu-jobs';
    app.commands.addCommand(command, {
      label: 'Show Jobs',
      caption: 'Show SkyPort jobs of the current user',
      execute: (args: any) => {
        create_main_area_widget("swm-jupyter-terminal:jobs", "SkyPort Jobs", app);
      }
    });
    palette.addItem({
      command,
      category,
      args: { origin: 'Show SkyPort jobs' }
    });
    skyport_menu.addItem({ command, args: { origin: 'SkyPort' } });
}

function add_config_resources(skyport_menu: Menu, palette: ICommandPalette, app: JupyterFrontEnd) {
    const category = 'SkyPort';
    const command = 'swm-jupyter-terminal:main-menu-res';
    app.commands.addCommand(command, {
      label: 'Show Resources',
      caption: 'Show SkyPort resources',
      execute: (args: any) => {
        create_main_area_widget("swm-jupyter-terminal:res", "SkyPort Resources", app);
      }
    });
    palette.addItem({
      command,
      category,
      args: { origin: 'Show SkyPort resources' }
    });
    skyport_menu.addItem({ command, args: { origin: 'SkyPort' } });
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
}
