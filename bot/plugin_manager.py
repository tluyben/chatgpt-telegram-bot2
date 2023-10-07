import subprocess
import json
import os
import asyncio

from plugins.gtts_text_to_speech import GTTSTextToSpeech
from plugins.dice import DicePlugin
from plugins.youtube_audio_extractor import YouTubeAudioExtractorPlugin
from plugins.ddg_image_search import DDGImageSearchPlugin
from plugins.ddg_translate import DDGTranslatePlugin
from plugins.spotify import SpotifyPlugin
from plugins.crypto import CryptoPlugin
from plugins.weather import WeatherPlugin
from plugins.ddg_web_search import DDGWebSearchPlugin
from plugins.wolfram_alpha import WolframAlphaPlugin
from plugins.deepl import DeeplTranslatePlugin
from plugins.worldtimeapi import WorldTimeApiPlugin
from plugins.whois_ import WhoisPlugin
from plugins.webshot import WebshotPlugin
from plugins.github import GithubPlugin


class PluginManager:
    """
    A class to manage the plugins and call the correct functions
    """

    def __init__(self, config):
        self.config = config
        enabled_plugins = config.get('plugins', [])
        plugin_mapping = {
            'wolfram': WolframAlphaPlugin,
            'weather': WeatherPlugin,
            'crypto': CryptoPlugin,
            'ddg_web_search': DDGWebSearchPlugin,
            'ddg_translate': DDGTranslatePlugin,
            'ddg_image_search': DDGImageSearchPlugin,
            'spotify': SpotifyPlugin,
            'worldtimeapi': WorldTimeApiPlugin,
            'youtube_audio_extractor': YouTubeAudioExtractorPlugin,
            'dice': DicePlugin,
            'deepl_translate': DeeplTranslatePlugin,
            'gtts_text_to_speech': GTTSTextToSpeech,
            'whois': WhoisPlugin,
            'webshot': WebshotPlugin,
            'github': GithubPlugin
        }
        self.plugins = [plugin_mapping[plugin]() for plugin in enabled_plugins if plugin in plugin_mapping]

    def get_dynamic_plugins(self):
        """
        Return the list of dynamic plugins
        """
        dynplugins = []
        if self.config['dynamic_plugins']:
             with open('./bot/dynamic_plugins.json', 'r') as file:
                dynplugins = json.load(file)
        return dynplugins
    
    def get_dynamic_plugins_as_text(self): 
        """
        Return the list of dynamic plugins as text
        """
        dynplugins = self.get_dynamic_plugins()
        # get the specs of the dynamic plugins; 
        specs = [] 
        for plugin_name in dynplugins:
            specs.append(self.get_dynamic_plugin_cli_spec(plugin_name))
        return "\n".join([f"{i+1}. {spec}" for i, spec in enumerate(specs)])
    
    def get_dynamic_plugin_spec(self, plugin_name):
        """
        Return the spec of a dynamic plugin
        """
        path = './bot/dynplugins/'+plugin_name
        if not os.path.exists(path):
            return None
        output = subprocess.check_output([path, '--help'])
        output_str = output.decode('utf-8')
        data = json.loads(output_str)
        return data 
    
    def get_dynamic_plugin_cli_spec(self, plugin_name):
        """
        Return the spec of a dynamic plugin
        """
        path = './bot/dynplugins/'+plugin_name
        if not os.path.exists(path):
            return None
        output = subprocess.check_output([path, '--cli-help'])
        output_str = output.decode('utf-8')
        #data = json.loads(output_str)
        return output_str 
    
    def get_dynamic_plugin_source_name(self, plugin_name):
        """
        Return the spec of a dynamic plugin
        """
        path = './bot/dynplugins/'+plugin_name
        if not os.path.exists(path):
            return None
        output = subprocess.check_output([path, '--name'])
        output_str = output.decode('utf-8')
        return output_str.strip()
    
    def get_function_to_plugin_mapping(self): 
        """
        Return the mapping of functions to plugins
        """
        mapping = {}
        for plugin in self.plugins:
            for spec in plugin.get_spec():
                mapping[spec['name']] = {"type": "static", "name": plugin.get_source_name(), "file": "d/c", "plugin": plugin}
        if self.config['dynamic_plugins']:
            # append the specs of the dynamic plugins
            dynplugins = self.get_dynamic_plugins()
            for plugin_name in dynplugins:
                for func in self.get_dynamic_plugin_spec(plugin_name):
                    mapping[func['name']] = {"type": "dynamic", "name": self.get_dynamic_plugin_source_name(plugin_name), "file": plugin_name,"plugin": None}
        return mapping 

    def get_plugin_by_function_name(self, function_name):
        """
        Return the plugin that has the function with the given name
        """
        mapping = self.get_function_to_plugin_mapping()
        if function_name in mapping:
            return mapping[function_name]
        return None

    def get_dynamic_cli_specs(self, function_name):
        """
        Return the specs of the dynamic plugin that has the function with the given name
        """
        mapping = self.get_function_to_plugin_mapping()
        if function_name in mapping and mapping[function_name]["type"] == "dynamic":
            return self.get_dynamic_plugin_cli_spec(mapping[function_name]["file"])
        return None

    def is_dynamic_plugin(self, function_name):
        """
        Return true if the function is a dynamic plugin
        """
        mapping = self.get_function_to_plugin_mapping()
        if function_name in mapping and mapping[function_name]["type"] == "dynamic":
            return True
        return False

    def get_functions_specs(self):
        """
        Return the list of function specs that can be called by the model
        """
        the_specs = [spec for specs in map(lambda plugin: plugin.get_spec(), self.plugins) for spec in specs]
        if self.config['dynamic_plugins']:
            # append the specs of the dynamic plugins
            dynplugins = self.get_dynamic_plugins()
            for plugin_name in dynplugins:
                for func in self.get_dynamic_plugin_spec(plugin_name):
                    the_specs.append(func)
        return the_specs

    def call_cli_function(self, function_name, arguments): 
        """ 
        Call a function based on the name and parameters provided
        """
        plugin = self.get_plugin_by_function_name(function_name)
        if plugin["type"] == "static":
            return "Cannot call a dynamic plugin as function"
        else: 
            # dynamic plugin
            path = './bot/dynplugins/'+plugin["file"]
            if not os.path.exists(path):
                return json.dumps({'error': f'Function {function_name} not found'})
            output = subprocess.check_output([path, "--cli", arguments])
            output_str = output.decode('utf-8')
            return json.dumps(output_str.strip())
        

    async def call_function(self, function_name, arguments):
        """
        Call a function based on the name and parameters provided
        """
        #plugin = self.__get_plugin_by_function_name(function_name)
        plugin = self.get_plugin_by_function_name(function_name)
        if not plugin:
            return json.dumps({'error': f'Function {function_name} not found'})
        
        if plugin["type"] == "static":
            return json.dumps(await plugin.execute(function_name, **json.loads(arguments)), default=str)
        else: 
            # dynamic plugin
            path = './bot/dynplugins/'+plugin["file"]
            if not os.path.exists(path):
                return json.dumps({'error': f'Function {function_name} not found'})
            output = subprocess.check_output([path, json.dumps(arguments).strip()])
            output_str = output.decode('utf-8')
            return json.dumps(output_str.strip())

    def get_plugin_source_name(self, function_name) -> str:
        """
        Return the source name of the plugin
        """

        plugin = self.get_plugin_by_function_name(function_name)

        #plugin = self.__get_plugin_by_function_name(function_name)
        if not plugin:
            return ''
        return plugin["name"]

    # def __get_plugin_by_function_name(self, function_name):
    #     return next((plugin for plugin in self.plugins
    #                  if function_name in map(lambda spec: spec.get('name'), plugin.get_spec())), None)


async def testing():
    # instantiate the plugin manager
    plugin_manager = PluginManager({"plugins": ["weather", "webshot"], "dynamic_plugins": True})

    # get the normal plugin specs; 
    specs = plugin_manager.get_functions_specs()
    print(json.dumps(specs, indent=4))

    # get the list of dynamic plugins
    dynplugins = plugin_manager.get_dynamic_plugins()
    print(dynplugins)

    # get the source name of a dynamic plugin
    source_name = plugin_manager.get_dynamic_plugin_source_name(dynplugins[0])
    print("name", source_name)

    source_name = plugin_manager.get_plugin_source_name("hello_world")
    print("name", source_name)

    # get the spec of a dynamic plugin
    spec = plugin_manager.get_dynamic_plugin_spec(dynplugins[0])
    print(spec)

    # check for none existing 
    source_name = plugin_manager.get_dynamic_plugin_source_name('soepkip')
    if source_name is None:
        print('source_name is None')

    # get mappings; 
    mapping = plugin_manager.get_function_to_plugin_mapping()
    print(mapping)

    # call a function
    result = await plugin_manager.call_function("hello_world", {"name": "John"})
    print(result)

    # show the cli specs; 
    cli_specs = plugin_manager.get_dynamic_cli_specs("hello_world")
    print(cli_specs)

    # call a cli function
    result = plugin_manager.call_cli_function("hello_world", "Johan")
    print(result)

    # check if a function is a dynamic function 
    print(plugin_manager.is_dynamic_plugin("hello_world"))
    print(plugin_manager.is_dynamic_plugin("get_repos"))
    print(plugin_manager.is_dynamic_plugin("plurk"))

    # get the dynamic plugins as text
    print(plugin_manager.get_dynamic_plugins_as_text())

if __name__ == '__main__':

    loop = asyncio.get_event_loop()
    loop.run_until_complete(testing())
   
   