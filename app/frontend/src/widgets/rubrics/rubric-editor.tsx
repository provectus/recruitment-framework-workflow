import { useState } from "react";
import { useForm, useFieldArray, useWatch, type UseFormReturn } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { ChevronDown, ChevronUp, Plus, Trash2 } from "lucide-react";
import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import {
  Card,
  CardContent,
  CardHeader,
} from "@/shared/ui/card";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/shared/ui/alert-dialog";

const rubricCriterionSchema = z.object({
  name: z.string().min(1, "Name is required"),
  description: z.string(),
  weight: z.number().min(0).max(100),
  sort_order: z.number(),
});

const rubricCategorySchema = z
  .object({
    name: z.string().min(1, "Name is required"),
    description: z.string(),
    weight: z.number().min(0).max(100),
    sort_order: z.number(),
    criteria: z
      .array(rubricCriterionSchema)
      .min(1, "At least one criterion required"),
  })
  .refine(
    (cat) => cat.criteria.reduce((sum, c) => sum + c.weight, 0) === 100,
    { message: "Criterion weights must sum to 100%", path: ["criteria"] }
  );

const rubricStructureSchema = z
  .object({
    categories: z
      .array(rubricCategorySchema)
      .min(1, "At least one category required"),
  })
  .refine(
    (s) => s.categories.reduce((sum, c) => sum + c.weight, 0) === 100,
    { message: "Category weights must sum to 100%", path: ["categories"] }
  );

type FormValues = z.infer<typeof rubricStructureSchema>;

export interface RubricCriterion {
  name: string;
  description: string | null;
  weight: number;
  sort_order: number;
}

export interface RubricCategory {
  name: string;
  description: string | null;
  weight: number;
  sort_order: number;
  criteria: RubricCriterion[];
}

export interface RubricStructure {
  categories: RubricCategory[];
}

interface RubricEditorProps {
  defaultValue?: RubricStructure;
  onSubmit: (structure: RubricStructure) => void;
  onCancel: () => void;
  isSubmitting?: boolean;
}

function WeightIndicator({ total, label }: { total: number; label: string }) {
  const isValid = total === 100;
  return (
    <span
      className={`text-xs font-medium ${isValid ? "text-muted-foreground" : "text-destructive"}`}
    >
      {label}: {total}% / 100%
    </span>
  );
}

function CriterionRow({
  categoryIndex,
  criterionIndex,
  totalCriteria,
  form,
  move,
  remove,
}: {
  categoryIndex: number;
  criterionIndex: number;
  totalCriteria: number;
  form: UseFormReturn<FormValues>;
  move: (from: number, to: number) => void;
  remove: (index: number) => void;
}) {
  const { register, formState } = form;
  const criterionErrors =
    formState.errors.categories?.[categoryIndex]?.criteria;
  const fieldError = Array.isArray(criterionErrors)
    ? criterionErrors[criterionIndex]
    : undefined;

  return (
    <div className="flex items-start gap-2 p-3 border rounded-lg bg-muted/30">
      <div className="flex flex-col gap-1 pt-1">
        <button
          type="button"
          disabled={criterionIndex === 0}
          onClick={() => move(criterionIndex, criterionIndex - 1)}
          className="text-muted-foreground hover:text-foreground disabled:opacity-30 disabled:cursor-not-allowed"
          aria-label="Move criterion up"
        >
          <ChevronUp className="h-3 w-3" />
        </button>
        <button
          type="button"
          disabled={criterionIndex === totalCriteria - 1}
          onClick={() => move(criterionIndex, criterionIndex + 1)}
          className="text-muted-foreground hover:text-foreground disabled:opacity-30 disabled:cursor-not-allowed"
          aria-label="Move criterion down"
        >
          <ChevronDown className="h-3 w-3" />
        </button>
      </div>
      <div className="flex-1 grid grid-cols-2 gap-2">
        <div>
          <Label
            className="sr-only"
            htmlFor={`cat${categoryIndex}-crit${criterionIndex}-name`}
          >
            Criterion name
          </Label>
          <Input
            id={`cat${categoryIndex}-crit${criterionIndex}-name`}
            placeholder="Criterion name"
            {...register(
              `categories.${categoryIndex}.criteria.${criterionIndex}.name`
            )}
          />
          {fieldError?.name && (
            <p className="text-destructive text-xs mt-1">
              {fieldError.name.message}
            </p>
          )}
        </div>
        <div>
          <Label
            className="sr-only"
            htmlFor={`cat${categoryIndex}-crit${criterionIndex}-desc`}
          >
            Description
          </Label>
          <Input
            id={`cat${categoryIndex}-crit${criterionIndex}-desc`}
            placeholder="Description (optional)"
            {...register(
              `categories.${categoryIndex}.criteria.${criterionIndex}.description`
            )}
          />
        </div>
      </div>
      <div className="w-20 shrink-0">
        <Label
          className="sr-only"
          htmlFor={`cat${categoryIndex}-crit${criterionIndex}-weight`}
        >
          Weight %
        </Label>
        <Input
          id={`cat${categoryIndex}-crit${criterionIndex}-weight`}
          type="number"
          min={0}
          max={100}
          placeholder="%"
          {...register(
            `categories.${categoryIndex}.criteria.${criterionIndex}.weight`,
            { valueAsNumber: true }
          )}
        />
      </div>
      <Button
        type="button"
        variant="ghost"
        size="sm"
        onClick={() => remove(criterionIndex)}
        aria-label="Remove criterion"
        className="shrink-0"
      >
        <Trash2 className="h-3 w-3 text-destructive" />
      </Button>
    </div>
  );
}

function CategoryCard({
  categoryIndex,
  totalCategories,
  form,
  moveCategory,
  removeCategory,
  onConfirmDelete,
}: {
  categoryIndex: number;
  totalCategories: number;
  form: UseFormReturn<FormValues>;
  moveCategory: (from: number, to: number) => void;
  removeCategory: (index: number) => void;
  onConfirmDelete: (index: number) => void;
}) {
  const { register, control, formState } = form;

  const { fields, append, remove, move } = useFieldArray({
    control,
    name: `categories.${categoryIndex}.criteria`,
  });

  const criteriaValues = useWatch({
    control,
    name: `categories.${categoryIndex}.criteria`,
  });

  const criteriaTotal = (criteriaValues ?? []).reduce(
    (sum, c) => sum + (Number(c?.weight) || 0),
    0
  );

  const categoryName = useWatch({
    control,
    name: `categories.${categoryIndex}.name`,
  });

  const categoryErrors = formState.errors.categories?.[categoryIndex];
  const criteriaRootError =
    !Array.isArray(categoryErrors?.criteria) &&
    typeof categoryErrors?.criteria?.message === "string"
      ? categoryErrors.criteria.message
      : null;

  const handleAddCriterion = () => {
    append({
      name: "",
      description: "",
      weight: 0,
      sort_order: fields.length,
    });
  };

  const handleRemoveCategory = () => {
    if (fields.length > 0) {
      onConfirmDelete(categoryIndex);
      return;
    }
    removeCategory(categoryIndex);
  };

  return (
    <Card className="gap-3 py-4">
      <CardHeader className="px-4 pb-0 pt-0">
        <div className="flex items-start gap-2">
          <div className="flex flex-col gap-1 pt-1">
            <button
              type="button"
              disabled={categoryIndex === 0}
              onClick={() => moveCategory(categoryIndex, categoryIndex - 1)}
              className="text-muted-foreground hover:text-foreground disabled:opacity-30 disabled:cursor-not-allowed"
              aria-label="Move category up"
            >
              <ChevronUp className="h-4 w-4" />
            </button>
            <button
              type="button"
              disabled={categoryIndex === totalCategories - 1}
              onClick={() => moveCategory(categoryIndex, categoryIndex + 1)}
              className="text-muted-foreground hover:text-foreground disabled:opacity-30 disabled:cursor-not-allowed"
              aria-label="Move category down"
            >
              <ChevronDown className="h-4 w-4" />
            </button>
          </div>

          <div className="flex-1 grid grid-cols-2 gap-2">
            <div>
              <Label
                htmlFor={`cat${categoryIndex}-name`}
                className="sr-only"
              >
                Category name
              </Label>
              <Input
                id={`cat${categoryIndex}-name`}
                placeholder="Category name"
                {...register(`categories.${categoryIndex}.name`)}
              />
              {categoryErrors?.name && (
                <p className="text-destructive text-xs mt-1">
                  {categoryErrors.name.message}
                </p>
              )}
            </div>
            <div>
              <Label
                htmlFor={`cat${categoryIndex}-desc`}
                className="sr-only"
              >
                Description
              </Label>
              <Input
                id={`cat${categoryIndex}-desc`}
                placeholder="Description (optional)"
                {...register(`categories.${categoryIndex}.description`)}
              />
            </div>
          </div>

          <div className="w-20 shrink-0">
            <Label htmlFor={`cat${categoryIndex}-weight`} className="sr-only">
              Weight %
            </Label>
            <Input
              id={`cat${categoryIndex}-weight`}
              type="number"
              min={0}
              max={100}
              placeholder="%"
              {...register(`categories.${categoryIndex}.weight`, {
                valueAsNumber: true,
              })}
            />
          </div>

          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={handleRemoveCategory}
            aria-label="Remove category"
            className="shrink-0"
          >
            <Trash2 className="h-4 w-4 text-destructive" />
          </Button>
        </div>

        <div className="flex items-center gap-2 pl-7 mt-1">
          <span className="text-xs text-muted-foreground font-medium truncate">
            {categoryName || "Unnamed category"}
          </span>
          <span className="text-muted-foreground text-xs">·</span>
          <WeightIndicator total={criteriaTotal} label="Criteria" />
        </div>
      </CardHeader>

      <CardContent className="px-4 pt-0">
        {fields.length === 0 ? (
          <p className="text-muted-foreground text-xs py-2">
            No criteria yet. Add at least one.
          </p>
        ) : (
          <div className="space-y-2">
            {fields.map((field, criterionIndex) => (
              <CriterionRow
                key={field.id}
                categoryIndex={categoryIndex}
                criterionIndex={criterionIndex}
                totalCriteria={fields.length}
                form={form}
                move={move}
                remove={remove}
              />
            ))}
          </div>
        )}

        {criteriaRootError && (
          <p className="text-destructive text-xs mt-2">{criteriaRootError}</p>
        )}

        <Button
          type="button"
          variant="outline"
          size="sm"
          className="mt-3 w-full"
          onClick={handleAddCriterion}
        >
          <Plus className="h-3 w-3 mr-1" />
          Add Criterion
        </Button>
      </CardContent>
    </Card>
  );
}

function toFormValues(structure: RubricStructure): FormValues {
  return {
    categories: (structure.categories ?? []).map((cat) => ({
      ...cat,
      description: cat.description ?? "",
      criteria: (cat.criteria ?? []).map((crit) => ({
        ...crit,
        description: crit.description ?? "",
      })),
    })),
  };
}

function toRubricStructure(data: FormValues): RubricStructure {
  return {
    categories: data.categories.map((cat, catIdx) => ({
      name: cat.name,
      description: cat.description.trim() || null,
      weight: cat.weight,
      sort_order: catIdx,
      criteria: cat.criteria.map((crit, critIdx) => ({
        name: crit.name,
        description: crit.description.trim() || null,
        weight: crit.weight,
        sort_order: critIdx,
      })),
    })),
  };
}

function getWeightsError(
  categoriesValues: FormValues["categories"] | undefined,
): string | null {
  if (!categoriesValues || categoriesValues.length === 0) return null;
  const catTotal = categoriesValues.reduce(
    (sum, c) => sum + (Number(c?.weight) || 0),
    0,
  );
  if (catTotal !== 100) {
    return `Category weights must sum to 100% (currently ${catTotal}%)`;
  }
  for (const cat of categoriesValues) {
    const criteriaTotal = (cat?.criteria ?? []).reduce(
      (sum, c) => sum + (Number(c?.weight) || 0),
      0,
    );
    if (criteriaTotal !== 100) {
      return `Criterion weights in "${cat?.name || "Unnamed category"}" must sum to 100% (currently ${criteriaTotal}%)`;
    }
  }
  return null;
}

export function RubricEditor({
  defaultValue,
  onSubmit,
  onCancel,
  isSubmitting = false,
}: RubricEditorProps) {
  const [pendingDeleteIndex, setPendingDeleteIndex] = useState<number | null>(
    null,
  );

  const form = useForm<FormValues>({
    resolver: zodResolver(rubricStructureSchema),
    defaultValues: defaultValue
      ? toFormValues(defaultValue)
      : { categories: [] },
  });

  const { control, handleSubmit, formState } = form;

  const {
    fields: categoryFields,
    append,
    remove,
    move,
  } = useFieldArray({
    control,
    name: "categories",
  });

  const categoriesValues = useWatch({ control, name: "categories" });

  const categoryTotal = (categoriesValues ?? []).reduce(
    (sum, c) => sum + (Number(c?.weight) || 0),
    0,
  );

  const weightsError = getWeightsError(categoriesValues);

  const categoriesRootError =
    typeof formState.errors.categories?.message === "string"
      ? formState.errors.categories.message
      : formState.errors.categories?.root?.message ?? null;

  const handleAddCategory = () => {
    append({
      name: "",
      description: "",
      weight: 0,
      sort_order: categoryFields.length,
      criteria: [],
    });
  };

  const handleFormSubmit = handleSubmit((data) => {
    onSubmit(toRubricStructure(data));
  });

  const handleDeleteConfirmed = () => {
    if (pendingDeleteIndex !== null) {
      remove(pendingDeleteIndex);
      setPendingDeleteIndex(null);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold">Categories</h3>
        <WeightIndicator total={categoryTotal} label="Total" />
      </div>

      {categoryFields.length === 0 ? (
        <p className="text-muted-foreground text-sm py-4 text-center">
          No categories yet. Add at least one category to build the rubric.
        </p>
      ) : (
        <div className="space-y-3">
          {categoryFields.map((field, categoryIndex) => (
            <CategoryCard
              key={field.id}
              categoryIndex={categoryIndex}
              totalCategories={categoryFields.length}
              form={form}
              moveCategory={move}
              removeCategory={remove}
              onConfirmDelete={setPendingDeleteIndex}
            />
          ))}
        </div>
      )}

      {categoriesRootError && (
        <p className="text-destructive text-sm">{categoriesRootError}</p>
      )}

      <Button
        type="button"
        variant="outline"
        className="w-full"
        onClick={handleAddCategory}
      >
        <Plus className="h-4 w-4 mr-1" />
        Add Category
      </Button>

      <div className="flex flex-col gap-2 pt-2 border-t">
        {weightsError && (
          <p className="text-destructive text-xs text-right">{weightsError}</p>
        )}
        <div className="flex justify-end gap-2">
          <Button
            type="button"
            variant="outline"
            onClick={onCancel}
            disabled={isSubmitting}
          >
            Cancel
          </Button>
          <Button
            type="button"
            onClick={handleFormSubmit}
            disabled={isSubmitting || weightsError !== null}
          >
            {isSubmitting ? "Saving..." : "Save Rubric"}
          </Button>
        </div>
      </div>

      <AlertDialog
        open={pendingDeleteIndex !== null}
        onOpenChange={(open) => {
          if (!open) setPendingDeleteIndex(null);
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete category?</AlertDialogTitle>
            <AlertDialogDescription>
              This category has criteria that will also be deleted. This action
              cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleDeleteConfirmed}>
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
