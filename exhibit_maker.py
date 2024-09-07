"""
Create grade distribution exhibits. Accepts a path to CSV file downloaded from Canvas
and a module number. Typical usage:

    $ python3 \
        --csv-path=2024-06-16T1128_Grades-CIS189_30864.csv \
        --output-dir=/home/jtriz/temp \
        --module=5
        --cmap=winter

Upon completion, .PNG file of assignment scores will be written to the directory 
specified in --output-dir named as ModuleXX.png. 

Dependencies:
------------
- pandas
- numpy
- matplotlib

Author: James D. Triveri

"""
import argparse
import configparser
from pathlib import Path

import matplotlib as mpl
import matplotlib.cm as cm
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd



def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--csv-path", type=str,
        help="Path to csv file downloaded from Canvas",
        default=None
        )
    parser.add_argument(
        "--img-path", type=str,
        help="Path to write grade distribution exhibit .png file",
        default=None
        )
    parser.add_argument(
        "--module", type=int,
        help="Module for which to create grade distribution",
        default=None
        )
    parser.add_argument(
        "--cmap", type=str,
        help="Colormap to use for grade distribution exhibits. Full list available at https://matplotlib.org/stable/users/explain/colors/colormaps.html",
        default=None
        )
    parser.add_argument(
        "--course-desc", type=str,
        help="Course description used in exhibit supertitle",
        default=""
        )
    parser.add_argument(
        "-v", "--verbose", action="store_true", 
        help="Additional output"
        )
    
    # Read from settings.cfg.
    config = configparser.ConfigParser()
    config.read("settings.cfg")

    # Parse command line arguments. 
    argvs = parser.parse_args()

    if (course_desc := argvs.course_desc) is None:
        course_desc = config["global"].get("course_desc").strip()

    if (csv_path := argvs.csv_path) is None:
        csv_path = config["global"].get("csv_path").strip()
    
    if (img_path := argvs.img_path) is None:
        img_path = config["global"].get("img_path").strip()

    if (module := argvs.module) is None:
        module = config["global"].getint("module")

    if (cmap := argvs.cmap) is None:
        cmap = config["global"].get("cmap").strip()

    if (verbose := argvs.verbose) is False:
        verbose = config["global"].getboolean("verbose")

    
    if verbose: 
        print(f"course_desc : {course_desc}")
        print(f"csv_path    : {csv_path}")
        print(f"img_path    : {img_path}")
        print(f"module      : {module}")
        print(f"cmap        : {cmap}")
        print(f"verbose     : {verbose}")
        print("--------------------------------------")
        print(f"mpl.__version__ : {mpl.__version__}")
        print(f"np.__version__  : {np.__version__}")
        print(f"pd.__version__  : {pd.__version__}")


    # Load grades file from Canvas. 
    dfall = pd.read_csv(csv_path)

    dfpossible = (
        dfall.iloc[0,:]
        .filter(regex="^M")
        .to_frame()
        .reset_index(drop=False)
        .rename({"index": "desc", 0: "possible"}, axis=1)
    )

    dfpossible["desc"] = dfpossible["desc"].str.replace(r"\(\d*\)", "", regex=True)
    dfpossible["desc"] = dfpossible["desc"].str.strip()
    dfpossible[["assignment", "desc"]] = dfpossible["desc"].str.split(":", expand=True)
    dfpossible["desc"]  = dfpossible["desc"].str.strip()
    dfpossible["assignment"] = dfpossible["assignment"].str.strip()
    dfpossible[["module", "assignment"]] = dfpossible["assignment"].str.split(" ", expand=True)
    dfpossible["module"] = dfpossible["module"].str.strip()
    dfpossible = dfpossible[dfpossible.module!="Multiple"].reset_index(drop=True)
    dfpossible["module"] = dfpossible["module"].str.replace("M", "").astype(int)
    dfpossible["assignment"] = dfpossible["assignment"].str.strip()
    dfpossible = dfpossible.sort_values(["module", "assignment"])
    dfpossible = dfpossible.assign(n=dfpossible.groupby(["module"]).cumcount().astype(int))
    dfpossible = dfpossible.drop("assignment", axis=1).rename({"n": "assignment"}, axis=1)
    dfpossible["assignment"] = dfpossible["assignment"] + 1
    dfassign = dfpossible[["module", "assignment", "desc", "possible"]]
    dfassign = dfassign[dfassign.module==module].reset_index(drop=True)

    module_columns = [ii for ii in dfall.columns if ii.startswith(f"M{module}")]
    keep_columns = ["Student"] + module_columns
    df = dfall.iloc[1:,:][keep_columns]
    df = (
        df
        .melt(id_vars=['Student'], value_vars=module_columns)
        .rename({"variable": "desc", "value": "grade"}, axis=1)
    )
    df["desc"] = df["desc"].str.replace(r"\(\d*\)", "", regex=True)
    df[["module", "desc"]] = df["desc"].str.split(":", expand=True)
    df["desc"]  = df["desc"].str.strip()
    df["module"] = df["module"].str.split(" ", expand=True).iloc[:,:-1]
    df["module"]  = df["module"].str.strip()
    df["module"] = df["module"].str.replace("M", "").astype(int)
    df = df[["module", "desc", "grade"]]
    df = df[df.module==module].reset_index(drop=True)
    df["grade"] = df["grade"].fillna(0)
    df = df.merge(dfassign, on=["desc", "module"], how="left")
    df = df[["module", "assignment", "desc", "grade", "possible"]]

    # Create grade distribution exhibit.
    n_facets = dfassign.shape[0]

    # Default to winter colormap if specified colormap does not exist. 
    try:
        fcolors = mpl.colormaps.get_cmap(cmap)
    except ValueError:
        print(f"No colormap `{cmap}`: Using winter.")
        fcolors = mpl.colormaps.get_cmap("winter")
    finally:
        colors_rgba = [fcolors(ii) for ii in np.linspace(0, 1, n_facets)]
        colors_hex = [mpl.colors.to_hex(ii, keep_alpha=False) for ii in colors_rgba]

    # Adjust font sizes based on number of facets.
    facet_title_fontsize = 10 if n_facets <=3 else 9
    annot_fontsize = 10 if n_facets <= 3 else 9
    tick_label_fontsize = 9 if n_facets <= 3 else 8
    axis_label_fontsize = 9 if n_facets <= 3 else 8

    fig, ax = plt.subplots(1, n_facets, figsize=(11, 5.0), sharey=True, sharex=False, tight_layout=True) 

    for ii, color in enumerate(colors_hex):
        module = dfassign.at[ii, "module"]
        assign = dfassign.at[ii, "assignment"]
        desc = dfassign.at[ii, "desc"]
        possible = dfassign.at[ii, "possible"]
        nbr_students = df[(df.module==module) & (df.assignment==assign)].shape[0]
        dfgrades = pd.DataFrame(np.arange(0, possible + 1, dtype=int), columns=["grade"])
        gg = df[df.assignment==assign].groupby("grade", as_index=False).size()
        gg = dfgrades.merge(gg, on="grade", how="left").fillna(0).rename({"size": "n"}, axis=1)
        zs = int(gg[gg.grade==0]["n"].item())
        dfavg = gg[gg.grade!=0]
        avg_score = (dfavg.grade * dfavg.n).sum() / dfavg.n.sum()
        min_score = df[(df.assignment==assign) & (df.grade>0)]["grade"].min().item()
        max_score = df[df.assignment==assign].dropna(how="any")["grade"].max()
        gg = gg.assign(grade=gg["grade"].astype(str), n=gg["n"].astype(int))
        gg.plot.bar(ax=ax[ii], color=color)
        
        ax[ii].set_title(f"{desc}", fontsize=facet_title_fontsize, weight="normal")
        ax[ii].set_xticklabels(gg["grade"].values, rotation=0)
        ax[ii].set_xlabel("score", fontsize=axis_label_fontsize)
        ax[ii].set_ylabel("nbr. students", fontsize=axis_label_fontsize)
        ax[ii].tick_params(axis="x", which="major", direction='in', labelsize=tick_label_fontsize)
        ax[ii].tick_params(axis="y", which="major", direction='in', labelsize=tick_label_fontsize)
        ax[ii].xaxis.set_ticks_position("none")
        ax[ii].yaxis.set_ticks_position("none")

        missing = int(gg[gg.grade=="0"]["n"].item())
        prop_missing = missing / nbr_students
        avg_desc = f"- avg. score : {avg_score:.2f}"
        min_desc = f"- min. score : {min_score:.1f}"
        max_desc = f"- max. score : {max_score:.1f}"
        na_desc  = f"- non-submits: {missing} ({prop_missing:.0%})"

        ax[ii].annotate(
            avg_desc, xy=(.05, .925), xycoords="axes fraction", ha="left", va="bottom", 
            fontsize=annot_fontsize, rotation=0, weight="bold", color="#000000"
            ) 
        ax[ii].annotate(
            min_desc, xy=(.05, .875), xycoords="axes fraction", ha="left", va="bottom", 
            fontsize=annot_fontsize, rotation=0, weight="bold", color="#000000"
            ) 
        ax[ii].annotate(
            max_desc, xy=(.05, .825), xycoords="axes fraction", ha="left", va="bottom", 
            fontsize=annot_fontsize, rotation=0, weight="bold", color="#000000"
            ) 
        ax[ii].annotate(
            na_desc, xy=(.05, .775), xycoords="axes fraction", ha="left", va="bottom", 
            fontsize=annot_fontsize, rotation=0, weight="bold", color="#FF0000"
            ) 
        ax[ii].get_legend().remove()

    plt.suptitle(f"{course_desc} Module {module} Assignments", weight="bold", size=12)

    if not img_path.endswith(".png"):
        img_path = img_path.rstrip(".") + ".png"
    plt.savefig(img_path)



if __name__ == "__main__":

    main()


