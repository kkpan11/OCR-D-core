((BASH_VERSINFO<4 || BASH_VERSINFO==4 && BASH_VERSINFO[1]<4)) && \
    echo >&2 "bash $BASH_VERSION is too old. Please install bash 4.4 or newer." && \
    exit 1

## ### `ocrd__raise`
##
## Raise an error and exit.
ocrd__raise () {
    echo >&2 "ERROR: $1"; exit 127
}

## ### `ocrd__log`
##
## Delegate logging to `ocrd log`
ocrd__log () {
    local log_level="${ocrd__argv[log_level]:-}"
    if [[ -n "$log_level" ]];then
        ocrd -l "$log_level" log "$@"
    else
        ocrd log "$@"
    fi
}


## ### `ocrd__minversion`
##
## Ensure minimum version
# ht https://stackoverflow.com/posts/4025065
ocrd__minversion () {
    set -e
    local minversion_raw="$1"
    local version_raw=$(ocrd --version|sed 's/ocrd, version //')
    local version_mmp=$(echo "$version_raw" | grep -Eo '([0-9]+\.?){3}')
    local version_prerelease_suffix="${version_raw#$version_mmp}"
    if [[ -z $version_prerelease_suffix ]];then
      version_prerelease_suffix=0
    fi
    local minversion_mmp=$(echo "$minversion_raw" | grep -Eo '([0-9]+\.?){3}')
    local minversion_prerelease_suffix="${minversion_raw#$minversion_mmp}"
    if [[ -z $minversion_prerelease_suffix ]];then
      minversion_prerelease_suffix=0
    fi
    local IFS='.'
    version=($version_mmp)
    minversion=($minversion_mmp)
    # MAJOR > MAJOR
    if (( ${version[0]} > ${minversion[0]} ));then
        return
    # MAJOR == MAJOR
    elif (( ${version[0]} == ${minversion[0]} ));then
        # MINOR > MINOR
        if (( ${version[1]} > ${minversion[1]} ));then
            return
        # MINOR == MINOR
        elif (( ${version[1]} == ${minversion[1]} ));then
            # PATCH > PATCH
            if (( ${version[2]} > ${minversion[2]} ));then
                return
            elif (( ${version[2]} == ${minversion[2]}));then
              # Match prerelease suffix like a1, b1 alphabetically
              if [ "$version_prerelease_suffix" = "$minversion_prerelease_suffix" -o "$version_prerelease_suffix" \> "$minversion_prerelease_suffix" ]; then
                return
              fi
            fi
        fi
    fi
    ocrd__raise "ocrd/core is too old ($version_raw < $minversion_raw). Please update OCR-D/core"
}

## ### `ocrd__dumpjson`
##
## Output ocrd-tool.json.
##
## Requires `$OCRD_TOOL_JSON` and `$OCRD_TOOL_NAME` to be set:
##
## ```sh
## export OCRD_TOOL_JSON=/path/to/ocrd-tool.json
## export OCRD_TOOL_NAME=ocrd-foo-bar
## ```
##
ocrd__dumpjson () {
    ocrd ocrd-tool "$OCRD_TOOL_JSON" tool "$OCRD_TOOL_NAME" dump
}

##
## Output file resource path.
##
ocrd__resolve_resource () {
    ocrd ocrd-tool "$OCRD_TOOL_JSON" tool "$OCRD_TOOL_NAME" resolve-resource "$1"
}

##
## Output file resource content.
##
ocrd__show_resource () {
    ocrd ocrd-tool "$OCRD_TOOL_JSON" tool "$OCRD_TOOL_NAME" show-resource "$1"
}

##
## Output file resources names.
##
ocrd__list_resources () {
    ocrd ocrd-tool "$OCRD_TOOL_JSON" tool "$OCRD_TOOL_NAME" list-resources
}

## ### `ocrd__usage`
##
## Print usage
##
ocrd__usage () {
    declare -a _args=(ocrd-tool "$OCRD_TOOL_JSON" tool "$OCRD_TOOL_NAME" help)
    if [ -v ocrd__subcommand ];then
        _args+=($ocrd__subcommand)
    fi
    ocrd ${_args[@]}
}

## ### `ocrd__parse_argv`
##
## Expects an associative array ("hash"/"dict") `ocrd__argv` to be defined:
##
## ```sh
## declare -A ocrd__argv=()
## ```
ocrd__parse_argv () {
    set -e

    # if [[ -n "$ZSH_VERSION" ]];then
    #     print -r -- ${+ocrd__argv} ${(t)ocrd__argv}
    # fi
    if ! declare -p "ocrd__argv" >/dev/null 2>/dev/null ;then
        ocrd__raise "Must set \$ocrd__argv (declare -A ocrd__argv)"
    fi

    if ! declare -p "params" >/dev/null 2>/dev/null ;then
        ocrd__raise "Must set \$params (declare -A params)"
    fi

    if ! declare -p "params_json" >/dev/null 2>/dev/null ;then
        ocrd__raise "Must set \$params_json (declare params_json)"
    fi

    if [[ $# = 0 ]];then
        ocrd__usage
        exit 1
    fi

    ocrd__argv[debug]=false
    ocrd__argv[overwrite]=false
    ocrd__argv[profile]=false
    ocrd__argv[profile_file]=
    ocrd__argv[mets_server_url]=
    ocrd__argv[mets_file]="$PWD/mets.xml"

    local __parameters=()
    local __parameter_overrides=()

    if [[ $1 == 'worker' || $1 == 'server' ]];then
         ocrd__subcommand="$1" ; shift ;
    fi

    while [[ "${1:-}" = -* ]];do
        case "$1" in
            -l|--log-level) ocrd__argv[log_level]=$2 ; shift ;;
            --log-filename) exec 2> "$2" ; shift ;;
            -h|--help|--usage) ocrd__usage; exit ;;
            -J|--dump-json) ocrd__dumpjson; exit ;;
            -D|--dump-module-dir) echo $(dirname "$OCRD_TOOL_JSON"); exit ;;
            -C|--show-resource) ocrd__show_resource "$2"; exit ;;
            -L|--list-resources) ocrd__list_resources; exit ;;
            -p|--parameter)  __parameters+=(-p "$(ocrd__resolve_resource "$2" 2>/dev/null || echo "$2")") ; shift ;;
            -P|--parameter-override) __parameter_overrides+=(-P "$2" "$3") ; shift ; shift ;;
            -g|--page-id) ocrd__argv[page_id]=$2 ; shift ;;
            -O|--output-file-grp) ocrd__argv[output_file_grp]=$2 ; shift ;;
            -I|--input-file-grp) ocrd__argv[input_file_grp]=$2 ; shift ;;
            -w|--working-dir) ocrd__argv[working_dir]=$(realpath "$2") ; shift ;;
            -m|--mets) ocrd__argv[mets_file]=$(realpath "$2") ; shift ;;
            -U|--mets-server-url) ocrd__argv[mets_server_url]="$2" ; shift ;;
            --debug) ocrd__argv[debug]=true ;;
            --overwrite) ocrd__argv[overwrite]=true ;;
            --profile) ocrd__argv[profile]=true ;;
            --profile-file) ocrd__argv[profile_file]=$(realpath "$2") ; shift ;;
            -V|--version) ocrd ocrd-tool "$OCRD_TOOL_JSON" version; exit ;;
            --queue) ocrd__worker_queue="$2" ; shift ;;
            --database) ocrd__worker_database="$2" ; shift ;;
            --address) ocrd__worker_address="$2" ; shift ;;
            *) ocrd__raise "Unknown option '$1'" ;;
        esac
        shift
    done

    if [ -v ocrd__worker_queue -o -v ocrd__worker_database -o -v ocrd__subcommand -o -v ocrd__worker_address ]; then
        if ! [ -v ocrd__subcommand ] ; then
            ocrd__raise "Provide subcommand 'worker' or 'server' for Processing Worker / Processor Server"
        elif ! [ -v ocrd__worker_database ]; then
            ocrd__raise "For the Processing Worker / Processor Server --database is required"
        fi
        if [ ${ocrd__subcommand} = "worker" ]; then
            if ! [ -v ocrd__worker_queue ]; then
                ocrd__raise "For the Processing Worker --queue is required"
            fi
            ocrd network processing-worker $OCRD_TOOL_NAME --queue "${ocrd__worker_queue}" --database "${ocrd__worker_database}"
        elif [ ${ocrd__subcommand} = "server" ]; then
            if ! [ -v ocrd__worker_address ]; then
                ocrd__raise "For the Processor Server --address is required"
            fi
            ocrd network processor-server $OCRD_TOOL_NAME --database "${ocrd__worker_database}" --address "${ocrd__worker_address}"
        else
            ocrd__raise "subcommand must be either 'worker' or 'server' not '${ocrd__subcommand}'"
        fi
        exit
    fi

    if [[ ! -e "${ocrd__argv[mets_file]}" ]]; then
        ocrd__raise "METS file '${ocrd__argv[mets_file]}' not found"
    fi

    if [[ ! -d "${ocrd__argv[working_dir]:=$(dirname "${ocrd__argv[mets_file]}")}" ]]; then
        ocrd__raise "workdir '${ocrd__argv[working_dir]}' not a directory. Use -w/--working-dir to set correctly"
    fi

    if [[ ! "${ocrd__argv[log_level]:=INFO}" =~ OFF|ERROR|WARN|INFO|DEBUG|TRACE ]]; then
        ocrd__raise "log level '${ocrd__argv[log_level]}' is invalid"
    fi

    if [[ -z "${ocrd__argv[input_file_grp]:=}" ]]; then
        ocrd__raise "Provide --input-file-grp/-I explicitly!"
    fi

    if [[ -z "${ocrd__argv[output_file_grp]:=}" ]]; then
        ocrd__raise "Provide --output-file-grp/-O explicitly!"
    fi

    # enable profiling (to be extended/acted upon by caller)
    if [[ ${ocrd__argv[profile]} = true ]]; then
        if [[ -n "${ocrd__argv[profile_file]}" ]]; then
            exec 3> "${ocrd__argv[profile_file]}"
        else
            exec 3>&2
        fi
        BASH_XTRACEFD=3
        # just the builtin tracer (without timing):
        #set -x
        # our own (including timing):
        DEPTH=+++++++++++
        shopt -s extdebug
        showtime() { date "+${DEPTH:0:$BASH_SUBSHELL+1} %H:%M:%S $BASH_COMMAND" >&3; }
        declare +t showtime # no trace here
        trap showtime DEBUG
    fi

    # check parameters
    local params_parsed retval
    params_parsed="$(ocrd ocrd-tool "$OCRD_TOOL_JSON" tool $OCRD_TOOL_NAME parse-params "${__parameters[@]}" "${__parameter_overrides[@]}")" || {
        retval=$?
        ocrd__raise "Failed to parse parameters (retval $retval):
$params_parsed"
    }
    eval "$params_parsed"
    params_json="$(ocrd ocrd-tool "$OCRD_TOOL_JSON" tool $OCRD_TOOL_NAME parse-params --json "${__parameters[@]}" "${__parameter_overrides[@]}")"

}

ocrd__wrap () {
    set -e

    declare -gx OCRD_TOOL_JSON="$1"
    declare -gx OCRD_TOOL_NAME="$2"
    shift
    shift
    declare -Agx params
    params=()
    declare -g params_json
    declare -Agx ocrd__argv
    ocrd__argv=()

    if ! which "ocrd" >/dev/null 2>/dev/null;then
        ocrd__raise "ocrd not in \$PATH"
    fi

    if ! declare -p "OCRD_TOOL_JSON" >/dev/null 2>/dev/null;then
        ocrd__raise "Must set \$OCRD_TOOL_JSON"
    elif [[ ! -r "$OCRD_TOOL_JSON" ]];then
        ocrd__raise "Cannot read \$OCRD_TOOL_JSON: '$OCRD_TOOL_JSON'"
    fi

   if [[ -z "$OCRD_TOOL_NAME" ]];then
        ocrd__raise "Must set \$OCRD_TOOL_NAME"
    elif ! ocrd ocrd-tool "$OCRD_TOOL_JSON" list-tools|grep -q "$OCRD_TOOL_NAME";then
        ocrd__raise "No such command \$OCRD_TOOL_NAME: $OCRD_TOOL_NAME"
    fi

    ocrd__parse_argv "$@"

    declare -ag ocrd__files
    IFS=$'\n'
    ocrd__files=( $(ocrd bashlib input-files \
                  --ocrd-tool $OCRD_TOOL_JSON \
                  --executable $OCRD_TOOL_NAME \
                  $(if [[ ${ocrd__argv[debug]} = true ]]; then echo --debug; fi) \
                  $(if [[ ${ocrd__argv[overwrite]} = true ]]; then echo --overwrite; fi) \
                  -m "${ocrd__argv[mets_file]}" \
                  -d "${ocrd__argv[working_dir]}" \
                  ${ocrd__argv[mets_server_url]:+-U} ${ocrd__argv[mets_server_url]:-} \
                  -p "$params_json" \
                  -I "${ocrd__argv[input_file_grp]}" \
                  -O "${ocrd__argv[output_file_grp]}" \
                  ${ocrd__argv[page_id]:+-g} ${ocrd__argv[page_id]:-}) )
    IFS=$' \t\n'
}

## usage: pageId=$(ocrd__input_file 3 pageId)
ocrd__input_file() {
    declare -A input_file
    eval input_file=( "${ocrd__files[$1]}" )
    eval echo "${input_file[$2]}"
}
