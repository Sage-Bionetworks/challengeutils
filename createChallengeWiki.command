#!/bin/bash
echo "This program only works for macs"
if command -v synapse; then 
    echo "synapseclient exists" 
else 
    echo "synapseclient does not exist"
    echo "Install syanpseclient? (y/n)" 
    read install
    if [ $install = 'y' ]; then 
        if command -v git; then
            echo "Installing synapseclient" 
            pip install synapseclient
        else
            echo "Please install pip: https://pip.pypa.io/en/stable/installing/"
            exit
        fi
    else 
        echo "You cannot run this program, because the synapseclient is not installed.  Please go here to learn how to install the develop version of synapseclient. (https://github.com/Sage-Bionetworks/synapsePythonClient#install-develop-branch)"
        exit
    fi
fi


echo "import synapseclient" > temp_syn_copy_Wiki.py
echo "import synapseutils as synu" >> temp_syn_copy_Wiki.py
echo "import getpass" >> temp_syn_copy_Wiki.py
echo "import sys" >> temp_syn_copy_Wiki.py
echo "if __name__ == '__main__':" >> temp_syn_copy_Wiki.py
echo "  synId = sys.argv[1]" >> temp_syn_copy_Wiki.py
echo "  try:" >> temp_syn_copy_Wiki.py
echo "      syn = synapseclient.login()" >> temp_syn_copy_Wiki.py
echo "  except Exception as e:" >> temp_syn_copy_Wiki.py
echo "      print('Please provide your synapse username/email and password (You will only be prompted once)')" >> temp_syn_copy_Wiki.py
echo "      Username = raw_input('Username: ')" >> temp_syn_copy_Wiki.py
echo "      Password = getpass.getpass()" >> temp_syn_copy_Wiki.py
echo "      syn = synapseclient.login(email=Username, password=Password,rememberMe=True)" >> temp_syn_copy_Wiki.py
echo "  synu.copyWiki(syn, 'syn2769515',synId)" >> temp_syn_copy_Wiki.py
echo "Synapse Challenge Page you want to create: "
read input_variable
python temp_syn_copy_Wiki.py $input_variable
echo "Created template"
synapse onweb $input_variable
rm temp_syn_copy_Wiki.py