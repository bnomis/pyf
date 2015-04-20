# add the dev directory to the path and pythonpath
if [ $_PYF_ACTIVATED ]; then
    echo 'Already activated'
else
    pwd=`pwd`
    export _PATH_BEFORE_PYF_ACTIVATE=$PATH
    export PATH=$pwd/dev:$PATH

    if [ ! -z $PYTHONPATH ]; then
        export _PYTHONPATH_BEFORE_PYF_ACTIVATE=$PYTHONPATH
        export PYTHONPATH=$pwd/dev:$PYTHONPATH
    else
        export _PYTHONPATH_BEFORE_PYF_ACTIVATE=0
        export PYTHONPATH=$pwd/dev
    fi

    export _PYF_ACTIVATED=1
fi
