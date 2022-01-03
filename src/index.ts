import { ICommandPalette, MainAreaWidget } from '@jupyterlab/apputils';

import { Menu, Widget } from '@lumino/widgets';

import { IMainMenu } from '@jupyterlab/mainmenu';

import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';

import { ISettingRegistry } from '@jupyterlab/settingregistry';

import { requestAPI } from './handler';

/**
 * Initialization data for the swm-jupyter-ext extension.
 */
const plugin: JupyterFrontEndPlugin<void> = {
  id: 'swm-jupyter-ext:plugin',
  autoStart: true,
  optional: [ISettingRegistry, ICommandPalette, IMainMenu],
  activate: (
    app: JupyterFrontEnd,
    settingRegistry: ISettingRegistry | null,
    palette: ICommandPalette,
    mainMenu: IMainMenu
  ) => {
    console.log('JupyterLab extension swm-jupyter-ext is activated!');

    if (settingRegistry) {
      settingRegistry
        .load(plugin.id)
        .then(settings => {
          console.log('swm-jupyter-ext settings loaded: ', settings.composite);
        })
        .catch(reason => {
          console.error(
            'Failed to load settings for swm-jupyter-ext.',
            reason
          );
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

function add_config_config(
  skyport_menu: Menu,
  palette: ICommandPalette,
  app: JupyterFrontEnd
) {
  const category = 'Sky Port';
  const command = 'swm-jupyter-ext:main-menu-config';
  app.commands.addCommand(command, {
    label: 'Configure Spawner',
    caption: 'Configure Sky Port',
    execute: (args: any) => {
      create_main_area_widget(
        'swm-jupyter-ext:config',
        'Sky Port Configuration',
        app
      );
    }
  });
  palette.addItem({
    command,
    category,
    args: { origin: 'Configure Sky Port' }
  });
  skyport_menu.addItem({ command, args: { origin: 'SkyPort' } });
}

function add_config_jobs(
  skyport_menu: Menu,
  palette: ICommandPalette,
  app: JupyterFrontEnd
) {
  const category = 'Sky Port';
  const command = 'swm-jupyter-ext:main-menu-jobs';
  app.commands.addCommand(command, {
    label: 'Show Jobs',
    caption: 'Show Sky Port jobs of the current user',
    execute: (args: any) => {
      const widget = create_main_area_widget(
        'swm-jupyter-ext:jobs',
        'Sky Port Jobs',
        app
      );
      fetch_jobs(widget);
    }
  });
  palette.addItem({
    command,
    category,
    args: { origin: 'Show Sky Port jobs' }
  });
  skyport_menu.addItem({ command, args: { origin: 'SkyPort' } });
}

function add_config_resources(
  skyport_menu: Menu,
  palette: ICommandPalette,
  app: JupyterFrontEnd
) {
  const category = 'Sky Port';
  const command = 'swm-jupyter-ext:main-menu-res';
  app.commands.addCommand(command, {
    label: 'Show Resources',
    caption: 'Show Sky Port resources',
    execute: (args: any) => {
      create_main_area_widget(
        'swm-jupyter-ext:res',
        'Sky Port Resources',
        app
      );
    }
  });
  palette.addItem({
    command,
    category,
    args: { origin: 'Show Sky Port resources' }
  });
  skyport_menu.addItem({ command, args: { origin: 'Sky Port' } });
}

function create_main_area_widget(
  id: string,
  label: string,
  app: JupyterFrontEnd
) {
  const content = new Widget();
  const widget = new MainAreaWidget({content});
  widget.addClass('SkyPortWidget');

  widget.id = id;
  widget.title.label = label;
  widget.title.closable = true;

  if (!widget.isAttached) {
    app.shell.add(widget, 'main');
  }
  app.shell.activateById(widget.id);

  return widget;
}

async function fetch_jobs(widget: MainAreaWidget) {
  console.log('Fetch Sky Port jobs');

  requestAPI<any>('get_jobs')
    .then(data => {
      print_jobs_table(widget, data);
    })
    .catch(reason => {
      console.error(
        `The swm_jupyter_ext server extension appears to be missing.\n${reason}`
      );
    });

}

function print_jobs_table(widget: MainAreaWidget, data: Array<Object>) {
  const table = document.createElement('table');
  table.setAttribute('border', '1');
  table.setAttribute('cellpadding', '6px');
  table.setAttribute('style', 'float:left');
  table.setAttribute('width', '100%');
  const table_body = document.createElement('tbody');

  const header_row = document.createElement('tr');
  add_table_cell(header_row, 'ID');
  add_table_cell(header_row, 'Name');
  add_table_cell(header_row, 'Submit');
  add_table_cell(header_row, 'Start');
  add_table_cell(header_row, 'End');
  add_table_cell(header_row, 'Nodes');
  add_table_cell(header_row, 'Resources');
  table_body.appendChild(header_row);

  for (let i in data) {
    const jobs = Object.values(data[i]);
    for (let j in jobs) {
      const job = jobs[j];
      const row = document.createElement('tr');

      add_table_cell(row, job.id);
      add_table_cell(row, job.name);
      add_table_cell(row, job.submit_time);
      add_table_cell(row, job.start_time);
      add_table_cell(row, job.end_time);
      add_table_cell(row, job.node_names);

      let resources: string[] = [];
      for (let n in job.request) {
        let res = job.request[n];
        let value: string = res.count;
        if ('value' in res) {
          value = res.value;
        }
        resources.push(res.name + "=" + value);
      }
      add_table_cell(row, resources.join(","));

      table_body.appendChild(row);
    }
  }
  table.appendChild(table_body);

  widget.node.appendChild(table);
}

function add_table_cell(row: Element, text: string) {
  const cell = document.createElement('td');
  const cell_text = document.createTextNode(text);
  cell.appendChild(cell_text);
  row.appendChild(cell);
}
